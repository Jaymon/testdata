import random
from collections.abc import Mapping, Iterable
from email.message import EmailMessage
from email.utils import formataddr, format_datetime, make_msgid, parseaddr

from datatypes import String

from .compat import *
from .base import TestData


class EmailData(TestData):
    def get_email_msgid(
        self,
        idstring: str = "",
        domain: str = "",
        *,
        msgid: str = "",
        **kwargs,
    ) -> str:
        """Very similar to `email.utils.make_msgid` but if `idstring` is passed
        in that is considered unique and will be used as the id portion of
        the msgid.

        A msgid is in the form of: `<idstring@domain>`

        https://docs.python.org/3/library/email.utils.html#email.utils.make_msgid
        """
        if msgid:
            if "@" not in msgid:
                raise ValueError(
                    "msgid needs to be in the form <ID>@<DOMAIN>",
                )

            ret = "<" + msgid.strip("<>") + ">"

        else:
            if not domain:
                domain = self.get_domain(**kwargs)

            if idstring:
                ret = f"<{idstring}@{domain}>"

            else:
                ret = make_msgid(idstring=idstring, domain=domain)

        return ret

    def create_email_message(
        self,
        data: str|dict[str, str] = "",
        subject: str = "",
        from_address: str = "",
        to_address: str|Iterable[str] = "",
        msgid: str = "",
        prev_msgids: Iterable[str]|str|None = None,
        headers: Mapping[str, str]|Iterable[tuple[str, str]]|None = None,
        **kwargs,
    ) -> EmailMessage:
        """Create an email message

        :param data: if just a string then it's considered to be `plain/text`,
            but it can also be a dict where the media_type is the key and the
            value is the content data for that media type
        :param headers: Any additional headers can be passed in here, usually
            as a mapping of header name as the keys and the header value as the
            values
        :returns:
            https://docs.python.org/3/library/email.message.html
        """
        if not from_address:
            if self.yes():
                from_address = formataddr((
                    self.get_name(),
                    self.get_email_address(),
                ))

            else:
                from_address = self.get_email_address()

        if not msgid:
            from_domain = from_address.split("@", 1)[1].rstrip(">")
            msgid = make_msgid(domain=from_domain)

        if not to_address:
            if self.yes():
                to_address = formataddr((
                    self.get_name(),
                    self.get_email_address(),
                ))

            else:
                to_address = self.get_email_address()

        if not subject:
            subject = self.get_words(min_size=1, max_size=10)

        if data:
            if isinstance(data, str):
                data["text/plain"] = data

        else:
            data = {"text/plain": self.get_words()}

        em = EmailMessage()

        em["From"] = from_address
        em["To"] = to_address
        em["Subject"] = subject
        em["Date"] = format_datetime(self.get_datetime(**kwargs))
        em["Message-ID"] = msgid

        if prev_msgids:
            if isinstance(prev_msgids, str):
                prev_msgids = [prev_msgids]

            prev_msgids = list(prev_msgids)
            for i in range(len(prev_msgids)):
                prev_msgids[i] = self.get_email_msgid(msgid=prev_msgids[i])

            em["In-Reply-To"] = prev_msgids[-1]
            em["References"] = " ".join(prev_msgids)

        if self.yes():
            # Delivered-To seems to be non-standard but common
            # https://www.postfix.org/virtual.8.html
            if isinstance(to_address, str):
                _, email_address = parseaddr(to_address)

            else:
                _, email_address = parseaddr(random.choice(list(to_address)))

            em["Delivered-To"] = email_address

        for media_type, content in data.items():
            if media_type == "text/plain":
                em.set_content(content)

            else:
                maintype, subtype = media_type.split("/", 1)
                em.add_alternative(
                    content,
                    maintype=maintype,
                    subtype=subtype,
                )

        if headers:
            if isinstance(headers, Mapping):
                headers = headers.items()

            for hn, hv in headers:
                if hn in em:
                    hn.replace_header(hn, hv)

                else:
                    em[hn] = hv

        return em

