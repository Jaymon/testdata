# -*- coding: utf-8 -*-
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
from testdata.server import TestDataServer


# def app_server(parsed):
#     pout.v("server")
# 
# 
# def app_function(parsed):
#     pout.v("function")
# 
# 
# class FunctionAction(argparse.Action):
#     # https://stackoverflow.com/questions/8632354/python-argparse-custom-actions-with-additional-arguments-passed
#     def __call__(self, parser, namespace, values, option_string=None):
# 
#         pout.v(parser, namespace, values, option_string)
#         setattr(namespace, self.dest, values)
#         #super().__call__(parser, args, values, option_string)


class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """Format help and keep newlines

    TODO -- Copied from captain.parse on 7-16-2024, this shouldn't be changed
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


class FunctionParser(argparse.ArgumentParser):
    def __init__(self, function_name, **kwargs):
        _function = getattr(testdata, function_name)

        if "description" not in kwargs:
            rf = ReflectCallable(_function)
            doc = rf.get_docblock()
            if doc:
                kwargs["description"] = "\n".join([
                    function_name,
                    "",
                    doc
                ])

        super().__init__(**kwargs)

        self.keyword_name = ""

        self.add_argument(
            "_function_name",
            metavar="FUNCTION_NAME",
            #action=FunctionAction,
            help="Testdata function name"
        )

        sig = inspect.signature(_function)
        for name, param in sig.parameters.items():
            arg_kwargs = {}
            if param.default is not param.empty:
                arg_kwargs["default"] = param.default

            if (
                param.kind is param.POSITIONAL_ONLY
                or param.kind is param.POSITIONAL_OR_KEYWORD
            ):
                if param.kind is not param.POSITIONAL_ONLY:
                    arg_kwargs["nargs"] = "?"

                self.add_argument(
                    name,
                    **arg_kwargs
                )

            if (
                param.kind is param.KEYWORD_ONLY
                or param.kind is param.POSITIONAL_OR_KEYWORD
            ):
                # https://docs.python.org/3/library/argparse.html#prefix-chars
                prefix = self.prefix_chars[0]

                if param.kind is param.KEYWORD_ONLY:
                    if "default" not in arg_kwargs:
                        arg_kwargs["required"] = True

                flags = [prefix*2 + name]
                kflag = prefix*2 + NamingConvention(name).kebabcase()
                if kflag not in flags:
                    flags.append(kflag)

                self.add_argument(
                    *flags,
                    dest=name,
                    **arg_kwargs
                )

            if param.kind is param.VAR_POSITIONAL:
                self.add_argument(
                    name,
                    nargs="*"
                )
            if param.kind is param.VAR_KEYWORD:
                self.keyword_name = name

        self.set_defaults(
            _function=_function,
        )




#                 self.add_argument(
#                     name,
#                     nargs="*"
#                 )


            #pout.v(name, param)


        #pout.i(function)
        #pout.v(inspect.signature(function))
        #pout.v(function.__defaults__)
        #pout.v(function.__kwdefaults__)


class ApplicationParser(argparse.ArgumentParser):
    """
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
#         self.add_argument(
#             "--debug", "-d",
#             action="store_true",
#             help="More verbose logging"
#         )

        self.add_argument(
            "_function_name",
            metavar="FUNCTION_NAME",
            #action=FunctionAction,
            help="Testdata function name"
        )


    def _parse_known_args(self, arg_strings, namespace):
        #pout.v(arg_strings)
        #pout.v(namespace)

        if arg_strings[0].startswith("-"):
            parsed, parsed_unknown = super()._parse_known_args(
                args,
                namespace
            )

        else:
            p = FunctionParser(
                arg_strings[0],
                formatter_class=self.formatter_class
            )
            parsed, parsed_unknown = p.parse_known_args(
                arg_strings,
                namespace
            )

            if p.keyword_name and parsed_unknown:
                setattr(
                    parsed, 
                    p.keyword_name,
                    UnknownParser(parsed_unknown).unwrap_keywords()
                )

        return parsed, parsed_unknown

#     def parse_args(self, *args, **kwargs):
#         parsed = super().parse_args(*args, **kwargs)
# 
#         _function_kwargs = {}
#         for name in parsed._argnames:
#             if name in parsed:
#                 _function_kwargs[name] = getattr(parsed, name)





    def xparse_known_args(self, args=None, namespace=None):
#         if args is None:
#             # args default to the system args
#             args = _sys.argv[1:]
# 
#         if args[0].startswith("-"):
#             parsed, parsed_unknown = super().parse_known_args(args, namespace)
# 
#         else:


        parsed, parsed_unknown = super().parse_known_args(args, namespace)

        pout.v(parsed.function_name)
        pout.v(parsed_unknown)

        return parsed, parsed_unknown



#     def format_help(self):
#         pout.v(self)
# 
#         return super().format_help()


def application():

    testdata.basic_logging()

    parser = ApplicationParser()

    parsed = parser.parse_args()
    rf = ReflectCallable(parsed._function)

    info = rf.get_bind_info(**dict(parsed._get_kwargs()))
    info["args"] = infer_type(info["args"])
    info["kwargs"] = infer_type(info["kwargs"])

    print(TestDataServer.run_method(
        parsed._function,
        *info["args"],
        **info["kwargs"]
    ))

    return 0



#     parsed, unknown = parser.parse_known_args()
#     return 0

    parser.add_argument(
        "--version", "-V",
        action='version',
        version="%(prog)s {}".format(testdata.__version__)
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="More verbose logging"
    )

    parser.add_argument(
        "function_name",
        nargs=1,
        metavar="FUNCTION_NAME",
        help="Testdata function name"
    )

#     parser.add_argument(
#         "function_args",
#         nargs="*",
#         metavar="FUNCTION_ARGS",
#         help="Testdata function positional arguments"
#     )

    parsed = parser.parse_args()
    rf = ReflectCallable(parsed._function)
    info = rf.get_bind_info(**dict(parsed._get_kwargs()))
    #pout.v(parsed)
    pout.v(info)
    return 0




    parser.set_defaults(app_callback=app_function)

    subparsers = parser.add_subparsers(dest="command", help="a sub command")
    #subparsers.required = False
    #subparsers.required = True # https://bugs.python.org/issue9253#msg186387

    # $ testdata server
    desc = "Start a testdata json server"
    subparser = subparsers.add_parser(
        "server",
        parents=[parser],
        help=desc,
        description=desc,
        conflict_handler="resolve",
    )
    subparser.set_defaults(app_callback=app_server)

    parsed, unknown = parser.parse_known_args()

    pout.v(unknown)
    parsed.app_callback(parsed)



    # $ testdata <FUNCTION-NAME> [<ARGS>, ...] [<KWARGS>, ...]
#     desc = "Run a testdata function and return its value"
#     subparser = subparsers.add_parser(
#         "server",
#         parents=[parser],
#         help=desc,
#         description=desc,
#         conflict_handler="resolve",
#     )
#     subparser.set_defaults(func=app_function)


if __name__ == "__main__":
    application()

