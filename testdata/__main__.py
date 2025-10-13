# -*- coding: utf-8 -*-
import asyncio
import argparse
import inspect
import textwrap

from datatypes import (
    ArgvParser as UnknownParser,
    ReflectCallable,
    infer_type,
    NamingConvention,
)

import testdata


class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """Format help and keep newlines

    !!! Copied from captain.parse on 7-16-2024, this shouldn't be changed
    here but should be changed/tested in captain and then re-copied to here,
    and the best would be to move it to datatypes
    """
    def _fill_text(self, text, width, indent):
        """Overridden to not get rid of newlines"""
        return "\n".join(self._split_lines(text, width, indent))

    def _split_lines(self, text, width, indent=""):
        """Overridden to not get rid of newlines

        :param text: str, the text
        :param width: int, how long each line can be
        :param indent: str, not in parent so has to have a default value
        :returns: list[str], the lines no more than width long
        """
        lines = []
        text = textwrap.dedent(text)
        for line in text.splitlines(False):
            if line:
                # https://docs.python.org/2/library/textwrap.html
                lines.extend(textwrap.wrap(
                    line,
                    width,
                    initial_indent=indent,
                    subsequent_indent=indent
                ))

            else:
                lines.append(line)

        return lines


class ParamAction(argparse.Action):
    """Mutually exclusive actions with a positional and optional with
    defaults and the same dest will overwrite the optional value with the
    default of the positional, so this custom action makes sure a non-default
    value in the namespace isn't overwritten by a default value
    """
    def __call__(self, parser, namespace, values, option_string=None):
        if self.dest in namespace:
            if values != self.default:
                setattr(namespace, self.dest, values)

        else:
            setattr(namespace, self.dest, values)


class FunctionParser(argparse.ArgumentParser):
    """Maps a testdata method to a parser definition so passed in CLI flags
    can be mapped to a testdata method call

    This is called from ApplicationParser and isn't meant to be used outside
    of that context
    """
    def __init__(self, _function, **kwargs):
        function_name = kwargs.pop("function_name", _function.__name__)

        rf = ReflectCallable(_function)
        self.keyword_name = ""
        param_descs = {}
        sig = rf.signature

        if "description" not in kwargs:
            kwargs["description"] = f"{function_name}{sig}"

            if rdoc := rf.reflect_docblock():
                param_descs = rdoc.get_param_descriptions()

                if desc := rdoc.get_description():
                    kwargs["description"] += "\n\n" + desc

        super().__init__(**kwargs)

        self.add_argument(
            "_function_name",
            metavar=function_name,
            choices=set([function_name]),
            help="The testdata function name",
        )

        for name, param in sig.parameters.items():
            arg_kwargs = {}

            arg_kwargs["metavar"] = name.upper()

            if name in param_descs:
                arg_kwargs["help"] = param_descs[name]

            if param.default is not param.empty:
                arg_kwargs["default"] = param.default

            if param.kind is param.POSITIONAL_OR_KEYWORD:
                # https://docs.python.org/3/library/argparse.html#mutual-exclusion
                group = self.add_mutually_exclusive_group(
                    required=("default" not in arg_kwargs),
                )

                group.add_argument(
                    name,
                    action=ParamAction,
                    nargs="?",
                    **arg_kwargs,
                )

                group.add_argument(
                    *self._get_flag_names(name),
                    action=ParamAction,
                    dest=name,
                    **arg_kwargs,
                )

            elif param.kind is param.POSITIONAL_ONLY:
                self.add_argument(
                    name,
                    **arg_kwargs,
                )

            elif param.kind is param.KEYWORD_ONLY:
                if "default" not in arg_kwargs:
                    arg_kwargs["required"] = True

                self.add_argument(
                    *self._get_flag_names(name),
                    dest=name,
                    **arg_kwargs
                )

            elif param.kind is param.VAR_POSITIONAL:
                self.add_argument(
                    name,
                    nargs="*",
                )

            elif param.kind is param.VAR_KEYWORD:
                self.keyword_name = name

        self.set_defaults(
            _function=_function,
        )

    def _get_flag_names(self, name):
        # https://docs.python.org/3/library/argparse.html#prefix-chars
        prefix = self.prefix_chars[0]

        flags = [prefix*2 + name]
        kflag = prefix*2 + NamingConvention(name).kebabcase()
        if kflag not in flags:
            flags.append(kflag)

        return flags


class ApplicationParser(argparse.ArgumentParser):
    """The main CLI parser. This basically is here to handle --help and 
    --version from the top level. If it has any other input it will defer
    to the FunctionParser

    I was originally going to have this be a default parser and then add a few
    subparsers for advanced functionality and I couldn't get that to work
    https://stackoverflow.com/a/46964652
    """
    def __init__(self, **kwargs):
        kwargs.setdefault("description", "testdata CLI")
        kwargs.setdefault("formatter_class", HelpFormatter)

        super().__init__(**kwargs)

        self.add_argument(
            "--version", "-V",
            action='version',
            version="%(prog)s {}".format(testdata.__version__)
        )

        self.add_argument(
            "_function_name",
            metavar="FUNCTION_NAME",
            help="Testdata function name"
        )

    def _parse_known_args(self, arg_strings, namespace, intermixed=False):
        """This is the internal method that is called from all the external
        methods

        If a flag is passed in then it will defer to parent's version of this
        method, if there is any other input then this defers to FunctionParser
        """
        # if there are any positionals defer to the function parser
        if filter(lambda s: not s.startswith("-"), arg_strings):
            _function = getattr(testdata, arg_strings[0])
            p = FunctionParser(
                _function,
                formatter_class=self.formatter_class,
            )

            parsed, parsed_unknown = p.parse_known_args(
                arg_strings,
                namespace,
            )

            if p.keyword_name and parsed_unknown:
                setattr(
                    parsed, 
                    p.keyword_name,
                    UnknownParser(parsed_unknown).unwrap_keywords(),
                )

        else:
            parsed, parsed_unknown = super()._parse_known_args(
                arg_strings,
                namespace,
                intermixed,
            )

        return parsed, parsed_unknown


async def application():
    """Callable for CLI application"""
    testdata.basic_logging()

    parser = ApplicationParser()

    parsed = parser.parse_args()
    rf = ReflectCallable(parsed._function)
    cb_kwargs = {k:v for k,v in parsed._get_kwargs() if v is not None}

    ret = await testdata.call_method(
        parsed._function_name,
        **infer_type(cb_kwargs),
    )

    print(testdata.get_jsonable_value(ret))

if __name__ == "__main__":
    asyncio.run(application())

