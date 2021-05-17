# Installing

## Requirements

To run Chiffee, you will first need Python 3, pip, venv, and Django installed on the server. To do so, run the 
following commands:
```
sudo apt-get install python3 python3-pip python3-venv
pip3 install django
```

LDAP also requires some packages installed on the server. To do so, run the following command:
```
sudo apt-get install libsasl2-dev python3-dev libldap2-dev libssl-dev
```

## Creating a Django project and virtual environment

To use Chiffee, we have to create a Django project first. This is done with the following command:
```
django-admin startproject mysite
```
This will create a `mysite` directory in your current directory.

Make sure to create a [virtual environment](https://docs.python.org/3/tutorial/venv.html) inside `mysite`, this will 
allow you to avoid any conflicts with existing system packages. We'll call the folder containing virtual environment 
`venv`:
```
python3 -m venv venv
```

## Cloning files from GitHub and installing required packages

Clone this repository:
```
git clone https://github.com/coffeecrank/chiffee.git
```

Now activate your virtual environment with `source venv/bin/activate` and install all packages listed 
[here](requirements.txt) by using the following commands in the exact same order:
```
pip3 install wheel
pip3 install -r requirements.txt
```

## Proxy

Installing with pip might be a problem if you're behind a proxy. In this case use the following command before 
downloading any pip packages:
```
export https_proxy=https://[username:password@]proxyserver:port
```
Check out [this](https://www.luis.uni-hannover.de/de/services/it-sicherheit/web-proxy/eckdaten-proxy-server/) article 
for instructions specific to the Leibniz University.

## Adding Chiffee URL's to your project

Now change the file `mysite/urls.py` by adding the following line to `urlpatterns`:
```
path('', include(('chiffee.urls', 'chiffee'), namespace='chiffee')),
```
This will add Chiffee URL's to your `mysite` project.

Also make sure to add these lines after `urlpatterns`:
```
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += i18n_patterns(path('admin/', admin.site.urls))
```

The resulting `mysite/urls.py` will look like this (don't forget 
to add an import for `include`):
```
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('chiffee.urls', 'chiffee'), namespace='chiffee')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += i18n_patterns(path('admin/', admin.site.urls))
```

## Adding environment variables

It's a good practice to store important settings in a separate file instead of hard-coding them.

Create a file named `.env` and place it in the root `mysite` directory (where `manage.py` is). This file should look 
like this (don't leave an empty blank line at the end): 
```
EMAIL_HOST='mailgate.uni-hannover.de'
SECRET_KEY='kj8qe5q#g8e8ks^b@p@!z@3js%ndq@h=lu+jqr7l%#fo1ph8%$'

AUTH_LDAP_SERVER_URI='ldap://myldap.de'
AUTH_LDAP_BIND_DN=''
AUTH_LDAP_BIND_PASSWORD=''
AUTH_LDAP_START_TLS=True
AUTH_LDAP_BASE_DN='dc=this,dc=is,dc=sparta'
AUTH_LDAP_OU_GROUPS='ou=groups'
AUTH_LDAP_CN_ADMINS='cn=mygroup'
AUTH_LDAP_USER_ATTR_MAP_USERNAME='uid'
AUTH_LDAP_USER_ATTR_MAP_FIRST_NAME='givenName'
AUTH_LDAP_USER_ATTR_MAP_LAST_NAME='sn'
AUTH_LDAP_USER_ATTR_MAP_EMAIL='mail'
AUTH_LDAP_MIRROR_GROUPS='group1 group2'
```
You should change all these settings accordingly.

You also want to import these environment variables when your project runs. Add the following line to `manage.py` 
inside the `main` function:
```
dotenv.load_dotenv()
```

It should look like this (don't forget the import):
```
import os
import sys

import dotenv


def main():
    dotenv.load_dotenv()

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
```

If you're using WSGI, then you also have to modify your `mysite/wsgi.py`: 
```
import os

import dotenv

dotenv.load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
```

## Changing settings.py

You can adjust your `mysite/settings.py` by taking a look at [this](coffee/settings.py) example file. Pay extra 
attention to the `Quick-start development settings` section.

## Collecting static (not that kind of static)

You want to collect your static files in one location when going to production. Navigate to where your `manage.py` is 
and run the following command:
```
python manage.py collectstatic
```

Make sure to read [this section](https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/modwsgi/#serving-files) on 
how to serve static files on your server.

## Migrating

### 1.x to 2.0

If you're moving to v2.0, follow these steps:
  - Back up current database file `db.sqlite3` in case something goes wrong.
  - Follow installation instructions as if it was a new project.
  - Copy your database file to the project root directory.
  - Now we need to update the database to the new design, this is where Django migrations come in.
  - You need to copy all your old migrations into the new project first. To do this, copy the folder 
    `chiffee/migrations` into your new project placing it under the same location. If your old project has no 
    migrations for some reason, then generate them with `python manage.py makemigrations`.
  - Navigate to your (new) project folder, activate virtual environment and run `python manage.py migrate --fake` which 
    makes Django think that old migrations have already been applied to the database (which is sort of true).
  - Now run `python manage.py makemigrations --empty chiffee` which will generate an empty migrations file inside 
    `chiffee/migrations`.
  - Open this file and replace the `operations` array with the following:
  ```
  operations = [
      migrations.RenameModel('Buy', 'Purchase'),

      migrations.RenameField('Product', 'product_name', 'name'),
      migrations.RenameField('Product', 'product_price', 'price'),
      migrations.RenameField('Product', 'product_active', 'active'),
      migrations.AddField('Product',
                          'category',
                          models.IntegerField(choices=CATEGORIES,
                                              default=1)),

      migrations.RenameField('Purchase', 'buy_date', 'date'),
      migrations.RenameField('Purchase', 'buy_count', 'quantity'),
      migrations.RenameField('Purchase', 'buy_product', 'product'),
      migrations.RenameField('Purchase', 'buy_user', 'user'),
      migrations.RenameField('Purchase', 'buy_total', 'total_price'),
      migrations.RemoveField('Purchase', 'buy_address'),
      migrations.AddField('Purchase',
                          'key',
                          models.CharField(max_length=64,
                                           default=generate_key)),

      migrations.RenameField('Deposit', 'deposit_date', 'date'),
      migrations.RenameField('Deposit', 'deposit_value', 'amount'),
      migrations.RenameField('Deposit', 'deposit_user', 'user'),

      migrations.RenameField('Employee', 'allMails', 'get_all_emails'),

      migrations.RunSQL("UPDATE chiffee_product "
                        + "SET category = 2 "
                        + "WHERE product_categorie = 'F'"),
      migrations.RunSQL("UPDATE chiffee_product "
                        + "SET category = 3 "
                        + "WHERE product_categorie = 'I'"),

      migrations.RemoveField('Product', 'product_categorie'),

      migrations.RunSQL("UPDATE auth_group "
                        + "SET name = 'professors' "
                        + "WHERE name = 'prof'"),
      migrations.RunSQL("UPDATE auth_group "
                        + "SET name = 'employees' "
                        + "WHERE name = 'wimi'"),
      migrations.RunSQL("UPDATE auth_group "
                        + "SET name = 'students' "
                        + "WHERE name = 'stud'"),
  ]
  ```
  - Change imports at the top of the file to match this:
  ```
  from django.db import migrations, models

  from chiffee.models import CATEGORIES, generate_key
  ```
  - Now run `python manage.py migrate`, and if you followed the steps correctly, the new migration will be applied with 
  no issues.
  
## Installing from scratch

If you're doing a fresh installation, run the following commands:
```
python manage.py makemigrations
python manage.py migrate
```


# LDAP

You can use LDAP to authenticate your users. Skip this section if you're not planning to use it.

## Changing settings.py

Make sure to take a look at [this](coffee/settings.py) example file for LDAP configuration help.

## Synchronizing automatically

The django command `syncldap` can synchronize LDAP users with the local database. New users from LDAP are added, and 
deleted users are marked inactive.
Some customizations may be necessary in `mysite/chiffee/management/commands/syncldap.py`.

Either execute the command manually or use a cronjob to sync, e.g. every day at 11.59 pm.
```
crontab -e
59 23 * * * cd /home/user/mysite/ && venv/bin/python3 manage.py syncldap
```


# Running

## Development

Use the following command to run a local development server:
```
python manage.py runserver
```

The output should look like this:
```
Performing system checks...

System check identified no issues (0 silenced).
February 20, 2018 - 16:24:58
Django version 1.11.4, using settings 'blub.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

## Production

The `runserver` command should only be used for development. Do not use it in production! 

If you want to use Django in production, there are several guides available. For example, 
[Apache](https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/modwsgi/).

Make sure to go through the official 
[Deployment checklist](https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/) as well.
