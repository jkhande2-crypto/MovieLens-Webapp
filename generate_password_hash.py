# A small, standalone python script whose only job is to take a password we type,
# scramble it using a one-way security function and print the scrambled result. 

# Why this file? 
# storing a plain readable password anywhere is a real risk, since one accidental share/backup,upload, etc exposes it permanently.
# One directional function - no reverse function that turns the hash back into the og password.
# When someone types a password to log in, the application doesn't "decrypt" the stored hash to comapare it.
# instead it runs the newly typed password thorugh the exact same one-way function again and
# checks whether the two scrambled result match.

"""
generate_password_hash.py - one time helper script.

Running this once to produce the value that goes into .env's ADMIN_ASSWORD_HASH line.
Never imported or used by the actual running application - exists purely to generate that 
one value, safly, w/o ever displaying the password on screen"""

import getpass  # buit-in python tool whose entie purpose is asking for input on screen w/o dsplaying what is typed.
from passlib.context import CryptContext  # bring the specific tool ( passlib - library, CryptContext- responsible for hashing it) that performs the one way hashing


# creating one configured hashing tool, telling it to use a specific, well-tested hashing algo called BCYRPT.
pwd_context = CryptContext( schemes = ["bcrypt"], deprecated = "auto") 


# asking for the password twice and comparing them - a std safegaurd against a simple typing mistake going unnoticed
password = getpass.getpass("Enter the admin password you want to use: ")
confirm = getpass.getpass(" Type it again to confirm: ")

if password != confirm:
    print(" The two entires did not match. Nothing was generated. Run the script again.")
else: 
    hashed = pwd_context.hash(password)  # one line that actually performs the one-way transformation - converting password to long, scrambled hash strings.
    print( "\n Copy the full line below into your .env file, replacing the existing ADMIN_PASSWORD_HASH line: \n")
    print(f"ADMIN_PASSWORD_HASH = {hashed}")


