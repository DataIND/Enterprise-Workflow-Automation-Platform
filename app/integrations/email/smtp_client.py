import smtplib


class SMTPClient:

    @staticmethod
    def send(email, subject, message):

        print(f"""
            Sending Email

            To:{email}

            Subject:{subject}

            {message}
            """)
