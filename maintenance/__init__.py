import sqlalchemy as sa
import random
import string
import re
from datetime import datetime

from api import get_subdomains_list
import conf


class PersonalData:

    def __init__(self, name: str, domain: str, country: str, allowed_domains):
        self.account = {
            'name': name,
        }
        self.engine = sa.create_engine(conf.MYSQL_CONNECTION_STRING, isolation_level="AUTOCOMMIT")
        self.allowed_domains = list(allowed_domains)
        self.domain = domain
        self._set_country_by_name(country)
        self._set_user_name_surname_from_name()
        self._set_email(domain)
        self._set_domain_id_by_name()
        self._set_birth_date()
        self._set_password()
        self._set_address_with_phone()
        self._set_personal_id()

    def _set_user_name_surname_from_name(self):
        user = self.account['name'].split(' ')

        if len(user) == 2:
            name = user[0]
            surname = user[1]
        elif len(user) > 2:
            name = user[0]
            surname = user[-1:][0]
        else:
            name = self.account['name']
            surname = ''
        with self.engine.connect() as conn:
            exists = conn.execute(
                sa.text('SELECT id FROM accounts WHERE name = :name AND surname = :surname'),
                {'name': name, 'surname': surname}
            ).scalar()
            assert exists is None, f'account with name {name} {surname} already exists {exists}'
        self.account.update({'name': name.capitalize(), 'surname': surname.capitalize()})
        return self

    def _set_email(self, domain):
        assert domain in self.allowed_domains, f'Domain {domain}  not present on host'
        name = self.account['name'].lower()
        surname = self.account['surname'].lower()
        if len(surname):
            email = f'{name}.{surname}@{self.account["country"].tag}.{domain}'
        else:
            email = f'{name}@{self.account["country"].tag}.{domain}'
        with self.engine.connect() as conn:
            exists = conn.execute(
                sa.text(f'SELECT id FROM accounts WHERE email = :email'), {'email': email}
            ).scalar()
            assert exists is None, f'email {email} already exists'
        self.account['email'] = email
        return self

    def _set_country_by_name(self, country):
        with self.engine.connect() as conn:
            country_row = conn.execute(
                sa.text(f""" SELECT id, name, tag, capital, prime FROM countries WHERE tag="{country}" """)
            ).fetchone()
            assert country_row is not None, f'country data not found for {country}'
            self.account['country'] = country_row
            self.account['country_id'] = country_row.id
        return self

    def _set_domain_id_by_name(self):
        with self.engine.connect() as conn:
            domain_id = conn.execute(sa.text(f"SELECT id FROM domains WHERE name='{self.domain}'")).scalar()
            assert domain_id is not None, f'domain id not found for {self.domain}'
            self.account['domain_id'] = domain_id
        return self

    def _set_address_with_phone(self):
        if not self.account['country'].id:
            return False
        mail_domains = ','.join([f"'{d.replace(f'.{conf.MAIN_DOMAIN}', '')}'" for d in self.allowed_domains])
        mail_domains_list = ','.join([d.replace(f'.{conf.MAIN_DOMAIN}', '') for d in self.allowed_domains])
        q_get_data = """
            SELECT cd.id FROM countries_data cd LEFT JOIN countries c ON cd.country_id = c.id
            WHERE cd.used_by_acc IS NULL AND cd.country_id = :country_id AND c.id IN(:tag)
            LIMIT 1 
        """
        with self.engine.connect() as conn:
            addr_id = conn.execute(sa.text(q_get_data),
                                   {'country_id': self.account['country'].id, 'tag': mail_domains}
                                   ).scalar()
            # print(f'\nADDR_ID: {addr_id}')
            if addr_id is None and self.account['country'].prime == 'is_city':
                # try to find another location in their area
                i = 0
                while addr_id is None and i < 3:
                    print(f'Try to find another address for {self.account["country"].name}')
                    addr_id = conn.execute(sa.text(f"""
                        SELECT cd.id, c.tag FROM countries c RIGHT JOIN countries_data cd
                        ON c.id = cd.country_id
                        WHERE cd.used_by_acc IS NULL AND c.capital = :capital AND c.prime = 'is_city' 
                        AND c.tag IN({mail_domains})
                        LIMIT 1
                    """), {'capital': self.account['country'].capital}).fetchone()
                    i += 1
                    print(f'ADDR_ID: {addr_id}')
                if addr_id is not None:
                    print(f"""
                        Founded free location for {self.account['country'].name}: {self.account['name']} {self.account['surname']} {addr_id}
                    """)
                    self._set_country_by_name(addr_id.tag)
                    self._set_email(self.domain)
                    self.account['address_id'] = addr_id.id
                    return self
            assert addr_id is not None, f'address not found for location {self.account["country"].name}'
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
        self.account['password'] = f"Pwd4{self.account['name']}.{self.account['surname']}"
        return self

    def generate_id(self):
        if self.account['country'].prime == 'is_city':
            city = self.account['country'].capital.lower()
            method_name = city.replace('-', '_') .replace(' ', '_') + '_personal_id'
        else:
            method_name = self.account['country'].tag.replace('-', '_') + '_personal_id'
        func = getattr(self, method_name)
        return func()

    def validate_id(self, personal_id):
        if self.account['country'].prime == 'is_city':
            city = self.account['country'].capital.lower()
            method_name = 'validate_' + city.replace('-', '_').replace(' ', '_') + '_personal_id'
        else:
            method_name = 'validate_' + self.account['country'].tag.replace('-', '_') + '_personal_id'
        func = getattr(self, method_name)
        return func(personal_id)

    def _set_personal_id(self):
        personal_id = self.generate_id()
        if self.validate_id(personal_id):
            self.account['personal_id'] = personal_id
        else:
            raise ValueError('personal ID is not valid')

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
        if len(personal_id) != 11:
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

    def algeria_personal_id(self):
        return ''

    def validate_algeria_personal_id(self, id_number):
        return True

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

    def angola_personal_id(self):
        # not implemented yet
        return ''

    def validate_angola_personal_id(self, id_number):
        # not implemented yet
        return True

    def antigua_and_barbuda_personal_id(self):
        # not implemented yet
        return ''

    def validate_antigua_and_barbuda_personal_id(self, id_number):
        # not implemented yet
        return True

    def argentina_personal_id(self):
        # not implemented yet
        return ''

    def validate_argentina_personal_id(self, id_number):
        # not implemented yet
        return True

    def armenia_personal_id(self):
        # not implemented yet
        return ''

    def validate_armenia_personal_id(self, id_number):
        # not implemented yet
        return True

    def azerbaijan_personal_id(self):
        # not implemented yet
        return ''

    def validate_azerbaijan_personal_id(self, id_number):
        # not implemented yet
        return True

    def bahamas_personal_id(self):
        # not implemented yet
        return ''

    def validate_bahamas_personal_id(self, id_number):
        # not implemented yet
        return True

    def bahrain_personal_id(self):
        # not implemented yet
        return ''

    def validate_bahrain_personal_id(self, id_number):
        # not implemented yet
        return True

    # The Austrian passport number is composed of two letters followed by seven digits.
    # The two letters at the beginning of the passport number are the country code for Austria, which is "AT."
    # The seven digits that follow are unique to each individual passport holder and are used to identify the passport.
    #
    # The rules for the formation of the seven-digit portion of the passport number are as follows:
    # The first digit is always a letter and represents the series of the passport.
    # It can be any letter except for "O" and "U", which are not used to avoid confusion with the numbers zero and one,
    # respectively.
    # The next two digits represent the issuing authority, which is usually a government agency or embassy.
    # The range of numbers used for this portion of the passport number is from 01 to 99.
    # The final four digits are a unique sequence of numbers assigned to each individual passport holder.
    # This sequence can be any combination of numbers and does not follow a specific pattern or rule.
    # For example, an Austrian passport number might look like this: AT A123 4567. In this example,
    # "A" represents the series of the passport, "12" represents the issuing authority,
    # and "3456" represents the unique sequence of numbers assigned to the passport holder.
    @staticmethod
    def austria_personal_id():
        # Generate a random digit for the series
        series = random.randint(1, 9)

        # Generate a random two-digit number for the issuing authority
        authority = random.randint(1, 99)
        authority_str = '{:02d}'.format(authority)

        # Generate a random four-digit number for the unique sequence
        sequence = random.randint(1, 9999)
        sequence_str = '{:04d}'.format(sequence)

        # Combine the parts to create the full ID number
        id_number = 'AT {}{}{}'.format(series, authority_str, sequence_str)
        return id_number

    @staticmethod
    def validate_austria_personal_id(id_number):
        # Check that the ID number matches the appropriate format
        pattern = r'^AT [1-9]\d{2}\d{4}$'
        if not re.match(pattern, id_number):
            return False
        return True

    # The national identification number used in Denmark is known as the CPR number (Central Person Register number).
    # The CPR number is a 10-digit number that consists of three different parts, separated by a hyphen,
    # in the following format:
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

    # https://learn.microsoft.com/en-us/microsoft-365/compliance/sit-defn-germany-passport-number?view=o365-worldwide
    # Format
    #
    # 9 to 11 characters
    # Pattern
    #
    #     one letter in C, F, G, H, J, K (case insensitive)
    #     eight digits or letters in C, F, G, H, J, K, L, M, N, P, R, T, V, W, X, Y and Z (case insensitive)
    #     optional check digit
    #     Optional d/D
    #
    # Checksum
    #
    # Yes
    def germany_personal_id(self):
        """
        """
        id_number = random.choice(['C', 'F', 'G', 'H', 'J', 'K'])
        digits_letters_8 = ''.join(random.choices(
            ['C', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'T', 'V', 'W', 'X', 'Y', 'Z'] + list(string.digits),
            k=8
        ))
        id_number += digits_letters_8
        id_number += str(random.randint(0, 9))
        id_number += ''.join(random.choices(['', 'D']))
        return id_number

    @classmethod
    def validate_germany_personal_id(cls, id_number):
        """
        Tests the generate_id_number function to ensure that test government ID numbers for Germany are being generated
        in the appropriate format.
        """
        # Test that the length of the ID number is 11
        if (len(id_number) < 9 or len(id_number) > 11 or id_number[0] not in ['C', 'F', 'G', 'H', 'J', 'K']
                or not all(char in string.ascii_uppercase + string.digits for char in id_number[1:9])):
            print(f'1: {id_number}')
            return False
        if len(id_number) == 10 and not id_number[9].isdigit():
            print(f'2: {id_number}')
            return False
        if len(id_number) == 11 and  id_number[-1] not in ['', 'D']:
            print(f'3: {id_number}')
            return False
        return True

    # the passport number is as follows:
    #
    # A A N N N N N N C
    #
    # Where:
    #
    #     A: two uppercase letters, representing the series code of the passport.
    #     N: six digits, representing the numerical part of the passport number.
    #     C: one alphanumeric character, representing the check digit.
    #
    # Example of a Turkish passport number:
    # AA123456B
    #
    # In this example, "AA" represents the series code, "123456" represents the numerical part,
    # and "B" represents the check digit.
    @classmethod
    def turkey_personal_id(cls):
        series_code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
        numerical_part = ''.join(random.choices('0123456789', k=6))
        check_digit = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        return f"{series_code}{numerical_part}{check_digit}"

    @classmethod
    def validate_turkey_personal_id(cls, id_number):
        if len(id_number) == 9 and id_number[:2].isalpha() and id_number[:2].isupper() and id_number[2:8].isdigit():
            return True
        return False

    # https://learn.microsoft.com/en-us/microsoft-365/compliance/sit-defn-italy-passport-number?view=o365-worldwide
    # Format
    #
    # two letters or digits followed by seven digits with no spaces or delimiters
    # Pattern
    #
    # two letters or digits followed by seven digits:
    #
    #     two digits or letters (not case-sensitive)
    #     seven digits
    #
    # Checksum
    #
    # not applicable

    @classmethod
    def italy_personal_id(cls):
        # Define the series letters for Italian passports
        series_letters = ['AA', 'BB', 'CC', 'DD', 'EE', 'FF', 'GG', 'HH', 'II', 'JJ']

        # Generate a random series letter and a six-digit number
        series = random.choice(series_letters)
        number = str(random.randint(100000, 999999))

        # Concatenate the series and number to create the passport number
        id_number = series + number
        return id_number

    @classmethod
    def validate_italy_personal_id(cls, id_number):
        pattern = r'^[A-Z]{2}\d{6}$'
        return re.match(pattern, id_number)

    # https://learn.microsoft.com/en-us/microsoft-365/compliance/sit-defn-portugal-passport-number?view=o365-worldwide
    # Format
    #
    # one letter followed by six digits with no spaces or delimiters
    # Pattern
    #
    # one letter followed by six digits:
    #
    #     one letter (not case-sensitive)
    #     six digits
    #
    # Checksum
    #
    # No

    @classmethod
    def portugal_personal_id(cls):
        # Define the series letters for Portuguese passports
        series_letters = ['A', 'B', 'C', 'D', 'E', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S', 'T', 'U', 'V', 'X',
                          'Y', 'Z']

        # Generate a random series letter and a seven-digit number
        series = random.choice(series_letters)
        number = str(random.randint(100000, 999999))

        # Concatenate the series and number to create the passport number
        id_number = series + number
        return id_number

    @classmethod
    def validate_portugal_personal_id(cls, id_number):
        pattern = r'^[A-Z]{1}\d{6}$'
        return re.match(pattern, id_number)

    # https://learn.microsoft.com/en-us/microsoft-365/compliance/sit-defn-us-uk-passport-number?view=o365-worldwide
    # Format
    #
    # nine digits
    # Pattern
    #
    #     one letter or digit
    #     eight digits
    #
    # Checksum
    #
    # No
    @classmethod
    def united_kingdom_personal_id(cls):
        # Define the alphabet for UK passport numbers
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

        # Generate two random letters and seven random digits
        letters = ''.join(random.choices(alphabet, k=2))
        digits = ''.join(random.choices('0123456789', k=7))

        # Concatenate the letters and digits to create the passport number
        id_number = letters + digits
        return id_number

    @classmethod
    def validate_united_kingdom_personal_id(self, id_number):
        pattern = r'^[A-Z]{2}\d{7}$'
        return re.match(pattern, id_number)

    # https://learn.microsoft.com/en-us/microsoft-365/compliance/sit-defn-spain-passport-number?view=o365-worldwide
    # Format
    #
    # an eight- or nine-character combination of letters and numbers with no spaces or delimiters
    # Pattern
    #
    # an eight- or nine-character combination of letters and numbers:
    #
    #     two digits or letters
    #     one digit or letter (optional)
    #     six digits
    #
    # Checksum
    #
    # Not applicable

    @classmethod
    def spain_personal_id(cls):
        digits = ''.join(random.choices('0123456789', k=8))
        letter = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        return digits + letter

    @classmethod
    def validate_spain_personal_id(cls, id_number):
        # Check that the passport number has exactly 9 characters
        if len(id_number) != 9:
            return False

        # Check that the first 8 characters are digits
        if not id_number[:8].isdigit():
            return False

        # Check that the last character is a letter
        if not id_number[8].isalpha():
            return False

        # Check that the last character is a capital letter
        if not id_number[8].isupper():
            return False

        # If all checks pass, the passport number is valid
        return True
