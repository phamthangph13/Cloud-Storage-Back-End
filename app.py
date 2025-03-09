from Authenticator import create_app
from flask import redirect

# Create the app with all controllers registered
app = create_app()

# Add a simple redirect for /trash to /api/trash
@app.route('/trash')
def trash_redirect():
    return redirect('/api/trash')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 