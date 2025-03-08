from Authenticator import create_app

# Create the app with all controllers registered
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)