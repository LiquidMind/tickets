## Initial filling of the database
### Loading countries lis
- `python -m maintenance.fill_countries --file data/countries.csv`

the file structure should be as follows:
```
name;capital;lat;lng
Turkey,Ankara,39.9199,32.8543,4919074
...
United Kingdom,London,51.5085,-0.1257,9046485
```

### Loading countries address from Google Maps API
- `python -m maintenance.load_countries_addresses`

addresses will be loaded for the locations that presents as mail subdomains (must be added beforehand, see [^1]) 

### Generating account
- `python -m maintenance.generate_personal_data --insert-accounts --file data/personal_data.csv`
the file structure should be as follows:
 ```
London;Martyn Morris
...
Glasgow;Lynda Stevens
```

### Getting not used account
- `python -m maintenance.accounts --get-free`
```
Result
id, name, surname, email, birth_date, personal_id, location(country/city), address, phone, prime 
(1114, 'Paula', 'Johann', 'paula.johann@berlin.chronisto.com', datetime.date(1972, 5, 14), 'KGZ4H4ML70', 'Berlin', 'Werderscher Markt 11, 10117 Berlin', '+49 30 4050461700', 'after_1000')
```

### Marking account as used
- `python -m maintenance.accounts --set-used --email paula.johann@berlin.chronisto.com`


## Mailbox API
[^1]: 
### Add domains DNS type A and MX records to hosting 
- `python main.py --add-domains --file data/personal_data.csv`

the file structure should be as follows:
 ```
location(country or city);account name
London;Martyn Morris
...
Glasgow;Lynda Stevens
```

#### Add main mailboxes for subdomains

- `python main.py --add-mailbox --file data/personal_data.csv`

- the file structure should be as follows:
 ```
location(country or city);account name
London;Martyn Morris
...
Glasgow;Lynda Stevens
```

#### Sets up a redirect from non-existent addresses to the main address of the subdomain

- `python main.py --update-subdomains`
