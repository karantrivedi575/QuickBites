from werkzeug.security import generate_password_hash

# Replace 'your_plaintext_password' with the password you want to use
hashed_password = generate_password_hash('admin1')
print(hashed_password)
