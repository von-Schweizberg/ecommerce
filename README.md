## Application Testing

The application has been tested with the latest version of the requirements (txt file), and there is no need to specify the version.

---

# Console Errors on Sign In/Sign Up Pages

The console errors on the sign-in/sign-up pages have no technical impact; they only affect the visual elements Google GSI library is trying to retrieve.

If you want to address these errors, uncomment the following line in `settings.py`:

```python
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
