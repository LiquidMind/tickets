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

addresses will be loaded for the locations that presents as mail subdomains (need be created before, see [^1]) 

### Generating account
- `python -m maintenance.generate_personal_data --insert-accounts --file data/personal_data.csv`
the file structure should be as follows:
 ```
London;Martyn Morris
...
Glasgow;Lynda Stevens
```

## Mailbox API
[^1]: 
- `python main.py --add-domains --file data/personal_data.csv`

#### TODO:

- `python main.py --add-mailbox --file data/personal_data.csv`

#### TODO:

- `python main.py --update-subdomains`

#### TODO:
