#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '0.1'

from getpass import getpass
from smtplib import SMTP

class Postbox(object):

    host = None
    port = None
    user = None
    password = None
    tls = True
    prompt_user = 'username? '
    prompt_password = 'password? '
    debuglevel = None
    dry_run = False

    def _update(self, attrs):
        for key, value in attrs.items():
            setattr(self, key, value)

    def __init__(self, **attrs):
        self.server = None
        self.connect(**attrs)

    def connect(self, **attrs):

        if attrs:
            self._update(attrs)

        self.server = SMTP(self.host, self.port)

        if self.debuglevel:
            self.server.set_debuglevel(self.debuglevel)

        if self.tls:
            self.server.starttls()

        if not self.user and self.prompt_user:
            self.user = raw_input(self.prompt_user)

        if self.user and not self.password and self.prompt_password:
            self.password = getpass(self.prompt_password)

        if self.user and self.password:
            self.server.login(self.user, self.password)

    def send(self, body, **headers_dict):

        sendmail_args = {'from': self.user, 'to': ''}
        headers = []

        for key, value in headers_dict.items():

            key = key.rstrip('_').lower().replace('_', '-')
            if key in sendmail_args:
                sendmail_args[key] = value

            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = ', '.join(value)

            headers.append('%s: %s' % (key, value))

        headers = '\r\n'.join(headers)

        if not self.dry_run:
            self.server.sendmail(


                sendmail_args['from'],
                sendmail_args['to'],
                '%s\r\n\r\n%s' % (headers, body)
            )

    def close(self):
        self.server.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

class Gmail(Postbox):
    host = 'smtp.gmail.com'
    port = '587'




from email.MIMEMultipart import MIMEMultipart # the wrapper of the whole msg
from email import Encoders                    # for attachments encoding 
from email.MIMEBase import MIMEBase           # the wrapper of the content
import os                                     # find the path of the attachments


class PostboxAtt(Postbox):
    """
    This class is a subclass of Postbox. It overrides sends method. Besides, it has attachBody and attachAttachments as its methods.

    Example usage of method send:

    mail.send(
            to = 'Lucas Ko <lucaskointw@gmail.com>',
            subject = 'first version of PostboxAtt',
            body    = 'Hey! First version!',
            attachments = ['<attachment_name in current dir>']
    )
    """
    def send(self, body, **headers):


        msg         = MIMEMultipart()   # wrap mail to MIME object

        msg['from'] = self.user         # msg headers initial declaration

        self.attachBody(msg, body)      # attach body as inline


        for key, value in headers.items():

            key = key.rstrip('_').lower().replace('_', '-') # for reply_to case
            if key == 'attachments':
                # attachments case
                self.attachAssignments(msg, value)

            elif hasattr(value, '__iter__') and not isinstance(value, str):
                # for those headers whose arguments is list
                value = ', '.join(value)
                msg[key] = value

            elif isinstance(value, str):
                # for those headers whose arguments is str
                msg[key] = value



        self.server.sendmail(
            msg['from'],
            msg['to'],
            msg.as_string())


    def attachBody(self, msg, body):
        """  attach body to the mime obj """
        content = MIMEBase('text', 'plain')                 # content-type
        content.set_payload(body)                           # set the body to the content
        content.add_header('Content-Disposition', 'inline')
        msg.attach(content)

        return msg



    def attachAssignments(self, msg, attachments):
        """ recursively attach enclosure to msg """

        for att in attachments:
            filename = att
            att = MIMEBase('application', 'octet-stream')
            att.set_payload( open(filename, "r").read() )

            Encoders.encode_base64(att) # for content-transfer-encoding

            # for each attachment, add headers
            att.add_header('Content-Disposition', 'attahment; filename="%s"' % os.path.basename(filename))
            msg.attach(att)

        return msg
