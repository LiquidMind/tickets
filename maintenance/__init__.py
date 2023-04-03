import sqlalchemy as sa
import random
import re
from datetime import datetime

import conf


class PersonalData:

    def __init__(self, email: str, country: str):
        self.account = {
            'email': email,
            'country': country,
        }
        self.engine = sa.create_engine(conf.MYSQL_CONNECTION_STRING, isolation_level="AUTOCOMMIT")
        self._set_country_id_by_name()
        self._set_user_name_surname_from_email()
        self._set_domain_id_by_name()
        self._set_birth_date()
        self._set_password()
        self._set_address_with_phone()

    def _set_user_name_surname_from_email(self):
        email_parts = self.account['email'].split('@')
        user_login = email_parts[0]
        user = user_login.split('.')

        if len(user) == 2:
            name = user[0]
            surname = user[1]
        elif len(user) > 2:
            name = user[0]
            surname = user[-1:][0]
        else:
            name = email_parts[0]
            surname = ''

        self.account.update({'name': name.capitalize(), 'surname': surname.capitalize()})
        return self

    def _set_country_id_by_name(self):
        with self.engine.connect() as conn:
            country_id = conn.execute(
                sa.text(f""" SELECT id FROM countries WHERE tag="{self.account['country']}" """)
            ).scalar()
        self.account['country_id'] = country_id
        return self

    def _set_domain_id_by_name(self):
        domain = self.account['email'].split('@')[1]
        with self.engine.connect() as conn:
            domain_id = conn.execute(sa.text(f"SELECT id FROM domains WHERE name='{domain}'")).scalar()
            self.account['domain_id'] = domain_id
        return self

    def _set_address_with_phone(self):
        if not self.account['country_id']:
            return False
        q_get_data = """
            SELECT id FROM countries_data
            WHERE used_by_acc IS NULL AND country_id = :country_id
            LIMIT 1 
        """
        with self.engine.connect() as conn:
            addr_id = conn.execute(sa.text(q_get_data), {'country_id': self.account['country_id']}).scalar()
            if addr_id is not None:
                self.account['address_id'] = addr_id
        return self

    def _set_birth_date(self):
        year = random.randrange(1970, 2000)
        month = random.randrange(1, 12)
        # if month < 10:
        #     month = f'0{month}'
        day = random.randrange(1, 28)
        # if day < 10:
        #     day = f'{0}{day}'
        self.account['birth_date'] = datetime.strptime(f'{year}-{month:02}-{day:02}', '%Y-%m-%d')
        return self

    def _set_password(self):
        return f"Pwd4{self.account['name']}.{self.account['surname']}"

    def generate_id(self):
        method_name = self.account['country'] + '_personal_id'
        func = getattr(self, method_name)
        return func()

    def validate_id(self, personal_id):
        method_name = 'validate_' + self.account['country'] + '_personal_id'
        func = getattr(self, method_name)
        return func(personal_id)

    def _set_personal_id(self):
        personal_id = self.generate_id()
        if self.validate_id(personal_id):
            self.account['personal_id'] = personal_id
        else:
            return False

    def afghanistan_personal_id(self):
        """
        To generate government ID numbers in Afghanistan, you can follow the following format:

        The first two digits represent the province code where the individual was born.
        The next six digits are the individual's date of birth in the format of YYMMDD.
        The last two digits represent the individual's gender, with odd numbers representing male and even numbers representing female.
        :return:
        """
        # Generate random province code (first two digits)
        province_code = f'{random.randint(1, 34):02}'

        # Generate random date of birth (next six digits)
        year = self.account['birth_date'].strftime('%y')
        month = self.account['birth_date'].strftime('%m')
        day = self.account['birth_date'].strftime('%d')
        dob = f'{year:02}{month:02}{day:02}'

        # Generate random gender code (last two digits)
        gender_code = random.choice([1, 3, 5, 7, 9]) if random.randint(0, 1) else random.choice([0, 2, 4, 6, 8])

        # Combine the parts to form the complete ID number
        id_number = f'{province_code}-{dob}{gender_code:02}'
        return id_number

    def validate_afghanistan_personal_id(self, personal_id):
        # check that the ID number is 11 characters long
        if len(spersonal_id) != 11:
            return False

        # check that the first two characters are valid province codes
        province_codes = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15',
                          '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
                          '31', '32', '33', '34']
        if personal_id[:2] not in province_codes:
            return False

        # check that the next 6 characters are digits
        if not personal_id[3:9].isdigit():
            return False

        # check that the last two characters are a valid gender code
        gender_code = int(personal_id[-2:])
        if gender_code % 2 == 0 and gender_code != 0:
            return True
        elif gender_code % 2 != 0:
            return True
        else:
            return False

    def albania_personal_id(self):
        """
        The government ID number format for Albania is as follows:

        The ID number is composed of 10 digits.
        The first two digits represent the year of birth (e.g. 98 for someone born in 1998).
        The next two digits represent the month of birth (e.g. 03 for someone born in March).
        The next two digits represent the day of birth (e.g. 25 for someone born on the 25th day of the month).
        The next digit represents the region code (e.g. 1 for Tirana, 2 for Durres, etc.).
        The last three digits represent a unique number assigned to the individual at birth
        (e.g. 123 for the 123rd child born on that day in that region).
        The last digit is a checksum digit calculated based on the first nine digits using a specific algorithm.

        This function generates a random Albanian government ID number by selecting random values for each part
        of the ID number (year, month, day, region code, gender, and unique number),
        formatting them appropriately, and then calculating and appending the checksum digit.
        The function does not use any external libraries, so it should work out-of-the-box in any Python environment.
        :return:
        """

        region_code = random.randint(1, 9)
        unique_number = random.randint(1, 99)

        # Format the parts of the ID number with leading zeros
        year_str = f"{self.account['birth_date'].strftime('%y'):02}"
        month_str = '{:02}'.format(self.account['birth_date'].strftime('%m'))
        day_str = '{:02}'.format(self.account['birth_date'].strftime('%d'))
        unique_number_str = '{:02d}'.format(unique_number)

        # Concatenate the parts of the ID number
        id_number = '{}{}{}{}{}'.format(year_str, month_str, day_str, region_code, unique_number_str)
        # print(year_str, month_str, day_str, region_code, unique_number_str)
        # Calculate the checksum digit
        checksum = 0
        for i, digit in enumerate(id_number):
            if i < len(id_number) - 1:
                checksum += (int(digit) * (i + 1))
        # print(f'1: {checksum}')
        checksum %= 11
        if checksum == 10:
            checksum = 0
        # print(f'2: {checksum}')
        # Append the checksum digit to the ID number
        id_number += str(checksum)
        return id_number

    def validate_albania_personal_id(self, id_number):
        # Remove any non-digit characters
        id_number = ''.join(filter(str.isdigit, id_number))
        # Check that the ID number is exactly 10 digits
        # print(id_number)
        if len(id_number) != 10:
            return False
        # Calculate the expected checksum using the Luhn algorithm
        s = sum(int(digit) * (index + 1) for index, digit in enumerate(id_number[:-2]))
        expected_checksum = s % 11
        if expected_checksum == 10:
            expected_checksum = 0
        # print(s)
        # print(f'expected: {expected_checksum}')
        # expected_checksum = (10 - s % 11) % 10
        # Check that the actual checksum matches the expected checksum
        actual_checksum = int(id_number[-1])
        return actual_checksum == expected_checksum

    #     The ID number is composed of 12 characters.
    #     The first three characters are the letter 'NAT', which stands for "national".
    #     The next two characters are the two-digit birth year of the person (e.g. "98" for someone born in 1998).
    #     The next two characters are the two-digit birth month of the person (e.g. "03" for someone born in March).
    #     The next two characters are the two-digit birth day of the person (e.g. "25" for someone born on the 25th day of the month).
    #     The next four characters are a unique identifier assigned by the government.
    #     The last character is a checksum digit calculated based on the first 11 characters using a specific algorithm.
    def andorra_personal_id(self):
        # Generate random birth date (between 18 and 80 years ago)
        birth_year = self.account['birth_date'].strftime('%y')
        birth_month = self.account['birth_date'].strftime('%m')
        birth_day = self.account['birth_date'].strftime('%d')

        # Generate random unique identifier (4 digits)
        unique_id = random.randint(0, 9999)

        # Format the parts of the ID number with leading zeros
        birth_year_str = str(birth_year)
        birth_month_str = f"{birth_month:02}"
        birth_day_str = f"{birth_day:02}"
        unique_id_str = f"{unique_id:04}"

        # Calculate the checksum digit
        id_number = f"NAT{birth_year_str}{birth_month_str}{birth_day_str}{unique_id_str}"
        checksum = 0
        for i, char in enumerate(id_number):
            if i < 11:
                weight = 7 - i if i < 7 else 9 - (i - 7)
                checksum += weight * ord(char)
        checksum %= 10

        # Append the checksum digit to the ID number
        id_number += str(checksum)
        return id_number

    def validate_andorra_personal_id(self, id_number):
        """
        Test function to check that Andorran government IDs are being generated in the correct format.
        """
        assert id_number[3:5] == self.account['birth_date'].strftime('%y'), f"ID number {id_number} does not match expected format (y)"
        assert id_number[5:7] == self.account['birth_date'].strftime('%m'), f"ID number {id_number} does not match expected format (m)"
        assert id_number[7:9] == self.account['birth_date'].strftime('%d'), f"ID number {id_number} does not match expected format (d)"
        checksum = 0
        for i, char in enumerate(id_number):
            if i < 11:
                weight = 7 - i if i < 7 else 9 - (i - 7)
                checksum += weight * ord(char)
        checksum %= 10
        assert str(checksum) == id_number[-1:], f"ID number {id_number} does not match expected format (checksum)"
        assert re.match(r'^[A-Z]{3}\d{11}$', id_number), f"ID number {id_number} does not match expected format"
        return True

    #     The ID number is composed of 9 digits.
    #     The first digit represents the gender and century of birth. It can be one of the following:
    #         1 for male born in the 20th century
    #         2 for female born in the 20th century
    #         3 for male born in the 21st century
    #         4 for female born in the 21st century
    #     The next two digits represent the birth day.
    #     The next two digits represent the birth month.
    #     The next two digits represent the last two digits of the birth year.
    #     The next two digits are the "serial number", a random number assigned by the government.
    #     The last digit is a checksum digit calculated based on the first eight digits using a specific algorithm.
    # def austria_personal_id(self):
    #     century = self.account['birth_date'].strftime('%Y')[:1]
    #     birth_year = self.account['birth_date'].strftime('%y')
    #
    #     # Generate birth month
    #     birth_month = f"{self.account['birth_date'].strftime('%m'):02}"
    #
    #     # Generate birth day
    #     birth_day = f"{self.account['birth_date'].strftime('%d'):02}"
    #
    #     # Generate birth order
    #     birth_order = '{:02d}'.format(random.randint(0, 99))
    #
    #     # Generate checksum
    #     id_number = birth_year + birth_month + birth_day + birth_order
    #     gender = random.choice(['F', 'M'])
    #     if gender == 'F':
    #         id_number += str(random.randint(0, 4) * 2)
    #     else:
    #         id_number += str(random.randint(1, 9))
    #
    #     weights = [3, 7, 9, 0, 5, 8, 4, 2, 1, 6]
    #     weighted_sum = sum([int(id_number[i]) * weights[i] for i in range(len(weights))])
    #     checksum = (11 - (weighted_sum % 11)) % 10
    #
    #     id_number += str(checksum)
    #
    #     return id_number
    #
    # def validate_austria_personal_id(self, id_number):
    #     assert re.match(r'^[1-2]\d{2}\d{2}\d{2}\d{2}$', id_number)

    # The national identification number used in Denmark is known as the CPR number (Central Person Register number). The CPR number is a 10-digit number that consists of three different parts, separated by a hyphen, in the following format:
    #
    # DDMMYY-SSSS
    #
    # where:
    #
    # DDMMYY: The date of birth of the person in the format of day, month, and year (in Danish format).
    # For example, if a person was born on March 25th, 1990, this part of the number would be 250390.
    #
    # SSSS: A four-digit number assigned by the Danish Civil Registration System to uniquely identify each individual.
    # The first digit of this part of the number is odd for males and even for females.
    #
    # The CPR number is a unique identification number assigned to every Danish citizen and residents of Denmark,
    # and it is used for various purposes, including tax administration, healthcare, social security,
    # and other government-related activities.
    def denmark_personal_id(self):
        # Generate a random date of birth
        day = self.account['birth_date'].strftime('%d')
        month = self.account['birth_date'].strftime('%m')
        year = self.account['birth_date'].strftime('%y')
        dob = "{:02}{:02}{:02}".format(day, month, year)

        # Generate a random four-digit number
        ssn = random.randint(0, 9999)
        ssn_str = "{:04d}".format(ssn)

        # Choose the gender based on the last digit of the four-digit number
        gender = "1" if ssn % 2 == 1 else "0"
        ssn_str = gender + ssn_str[1:]
        # Combine the date of birth and four-digit number with a hyphen
        cpr = dob + "-" + ssn_str

        # Calculate the check digit
        weights = [4, 3, 2, 7, 6, 5, 4, 3, 2, 1]
        print(cpr.replace('-', ''))
        products = [int(cpr.replace('-', '')[i]) * weights[i] for i in range(9)]

        # Calculate the checksum
        checksum = sum(products) % 11

        # If the checksum is 0, the check digit is 0, otherwise subtract it from 11
        check_digit = str(11 - checksum) if checksum != 0 else "0"

        # Append the check digit to the CPR number
        cpr += check_digit

        # Return the generated CPR number
        return cpr

    def validate_denmark_personal_id(self, cpr):
        # Check that the CPR number has the correct length
        assert len(cpr.replace('-', '')) == 11

        # Check that the CPR number contains a hyphen in the correct position
        assert cpr[6] == "-"

        # Check that the first six digits of the CPR number represent a valid date of birth
        dob = cpr[:6]
        assert dob == self.account['birth_date'].strftime('%d%m%y')

        # Check that the last four digits of the CPR number are between 0001 and 9999
        ssn = int(cpr[7:11])
        assert 1 <= ssn <= 9999

        # Check that the first digit of the last four digits of the CPR number is odd for males and even for females
        gender = int(cpr[7])
        print(gender)
        print(ssn)
        if gender % 2 == 1:
            assert ssn % 2 == 1
        else:
            assert ssn % 2 == 0

        # Check that the check digit is correct
        # Calculate the check digit
        weights = [4, 3, 2, 7, 6, 5, 4, 3, 2, 1]
        products = [int(cpr.replace('-', '')[i]) * weights[i] for i in range(10)]

        # Calculate the checksum
        checksum = sum(products) % 11

        # If the checksum is 0, the check digit is 0, otherwise subtract it from 11
        check_digit = str(11 - checksum) if checksum != 0 else "0"
        assert check_digit == cpr[-1]

        return True