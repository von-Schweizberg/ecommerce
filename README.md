## Application Testing

The application has been tested with the latest version of the requirements (txt file), and there is no need to specify the version.

#### Stripe API was tested locally with Stripe CLI and in production with real-time webhook.

---

# Testing in Local Enviroment

Google sign-in will work only with `localhost:8000`, not with `127.0.0.1:8000`

---

# Console Errors on Sign In/Sign Up Pages

The console errors on the sign-in/sign-up pages have no technical impact; they only affect the visual elements Google GSI library is trying to retrieve.

If you want to address these errors, uncomment the following line in `settings.py`

```python
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
```
