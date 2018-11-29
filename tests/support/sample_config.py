"""
Default settings. Override these with settings in the module pointed to
by the PROTEAN_CONFIG environment variable.
"""

####################
# CORE             #
####################

DEBUG = True

# A secret key for this particular Protean installation. Used in secret-key
# hashing algorithms.
SECRET_KEY = 'abcdefghijklmn'

# Flag indicates that we are testing
TESTING = True

# Define the repositories
REPOSITORIES = {
    'default': {
        'PROVIDER': 'protean_sqlalchemy.repository',
        'DATABASE_URI': 'sqlite:///:memory:'
    },
    'another_db': {
        'PROVIDER': 'protean_sqlalchemy.repository',
        'DATABASE_URI': 'sqlite:///:memory:'
    }
}
