from collections.abc import Mapping, Iterable
from email.message import EmailMessage
from email.utils import formataddr, format_datetime, make_msgid, parseaddr

from datatypes import String

from .compat import *
from .base import TestData


class EmailData(TestData):
    def create_email(
        self,
        data: str|dict[str, str] = "",
        subject: str = "",
        from_address: str = "",
        to_address: str = "",
        msg_id: str = "",
        prev_msg_ids: Iterable[str]|str|None = None,
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

        if not msg_id:
            from_domain = from_address.split("@", 1)[1].rstrip(">")
            msg_id = make_msgid(domain=from_domain)

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
        em["Message-ID"] = msg_id

        if prev_msg_ids:
            if isinstance(prev_msg_ids, str):
                prev_msg_ids = [prev_msg_ids]

            em["In-Reply-To"] = prev_msg_ids[-1]
            em["References"] = " ".join(prev_msg_ids)

        if self.yes():
            # Delivered-To seems to be non-standard but common
            # https://www.postfix.org/virtual.8.html
            name, email_address = parseaddr(to_address)
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

