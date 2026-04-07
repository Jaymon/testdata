import random
from collections.abc import Mapping, Iterable
from email.message import EmailMessage
from email.utils import formataddr, format_datetime, make_msgid, parseaddr
import datetime
import textwrap

from datatypes import String

from .compat import *
from .base import TestData


class EmailData(TestData):
    def get_email_address(
        self,
        name: str = "",
        domain: str = "",
        *,
        unique: bool = False,
        **kwargs,
    ) -> str:
        """return a random email address

        :keyword unique: If True then `name` will have a random suffix added
            to it to better guarrantee uniqueness, in practice, unless you
            are generating millions of email addresses this probably isn't
            needed to ever be True
        """
        name = self.get_username(name)
        if unique:
            name += "{:.6f}".format(time.time()).replace(".", "")

        if not domain:
            if self.yes():
                domain = random.choice([
                    "yahoo.com",
                    "hotmail.com",
                    "outlook.com",
                    "aol.com",
                    "gmail.com",
                    "msn.com",
                    "comcast.net",
                    "hotmail.co.uk",
                    "sbcglobal.net",
                    "yahoo.co.uk",
                    "yahoo.co.in",
                    "bellsouth.net",
                    "verizon.com",
                    "earthlink.net",
                    "cox.net",
                    "rediffmail.com",
                    "yahoo.ca",
                    "btinternet.com",
                    "charter.net",
                    "shaw.ca",
                    "ntlworld.com",
                    "gmx.com",
                    "gmx.net",
                    "mail.com",
                    "mailinator.com",
                    "icloud.com",
                ])

            else:
                domain = self.get_domain()

        return "{}@{}".format(name.lower(), domain)

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

        em = EmailMessage()

        em["From"] = from_address
        em["To"] = to_address
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

        if not subject:
            subject = self.get_words(min_size=1, max_size=10)

        if prev_msgids and not subject.startswith("Re:"):
            subject = ("Re: " * len(prev_msgids)) + subject

        em["Subject"] = subject

        if self.yes():
            # Delivered-To seems to be non-standard but common
            # https://www.postfix.org/virtual.8.html
            if isinstance(to_address, str):
                _, email_address = parseaddr(to_address)

            else:
                _, email_address = parseaddr(random.choice(list(to_address)))

            em["Delivered-To"] = email_address

        if data:
            if isinstance(data, str):
                data = {"text/plain": data}

        else:
            data = {"text/plain": self.get_words()}

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

    def create_email_thread(
        self,
        subject: str = "",
        from_address: str = "",
        to_address: str|Iterable[str] = "",
        count: int = 2,
        **kwargs,
    ) -> list[EmailMessage]:
        emails = []
        prev_msgids = []

        for _ in range(count):
            if emails:
                prev_msgids.append(emails[-1].get("Message-ID"))

                dt = datetime.datetime.strptime(
                    emails[-1].get("Date"),
                    "%a, %d %b %Y %H:%M:%S %z",
                )

                data = self.get_words()
                data += "\n\n"

                ds = dt.strftime("%a, %b %d, %Y at %I:%M %p")
                #from_addr = formataddr(parseaddr(emails[-1].get("From")))
                from_addr = emails[-1].get("From")
                data += f"On {ds} {from_addr} wrote:\n\n"

                data += textwrap.indent(
                    emails[-1].get_content(),
                    "> ",
                    lambda line: True,
                )

                emails.append(self.create_email_message(
                    subject=emails[0]["Subject"],
                    from_address=emails[-1]["To"],
                    to_address=emails[-1]["From"],
                    prev_msgids=prev_msgids,
                    data=data,
                    **kwargs,
                ))

            else:
                emails.append(self.create_email_message(
                    subject=subject,
                    from_address=from_address,
                    to_address=to_address,
                    **kwargs,
                ))

        return emails

