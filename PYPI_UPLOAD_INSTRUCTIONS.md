# How to Upload This Package to PyPI

If you have never uploaded a package to the Python Package Index (PyPI) before, don't worry! Modern Python tooling makes this process straightforward.

Follow these step-by-step instructions from your local repository to build and publish the `campaign-logger` package.

---

## Step 1: Create Your Accounts and API Tokens

1. **Register on PyPI:** If you don't have one, create an account on [pypi.org](https://pypi.org/account/register/).
2. **Enable 2FA:** PyPI now requires Two-Factor Authentication for security. Go to your account settings to enable it.
3. **Generate a PyPI API Token:**
   - Go to your Account Settings -> **API tokens**.
   - Click **Add API token**.
   - Name it something like "Campaign Logger CLI".
   - Set the Scope to "Entire account" (or to the specific project if it already exists).
   - **Copy the token and save it somewhere safe!** It will start with `pypi-`. You won't be able to see it again.
4. **(Optional but Recommended) TestPyPI:** You can also register on [test.pypi.org](https://test.pypi.org/account/register/) to do a practice run without affecting the official Python repository. Create a separate API token there.

---

## Step 2: Install Build Tools

Make sure you have the official Python packaging tools installed in your environment. Open your terminal at the root of this project and run:

```bash
python -m pip install --upgrade pip
python -m pip install --upgrade build twine
```

* `build`: The tool that creates the deployable archives (`.tar.gz` and `.whl`).
* `twine`: The tool that securely uploads these archives to PyPI.

---

## Step 3: Build the Package

Before uploading, you need to bundle your code into distributable formats (a source archive and a built distribution).

Run the following command in the root of the project (where `setup.py` is located):

```bash
python -m build
```

This will create a new directory called `dist/`. Inside it, you should see two files:
1. `campaign_logger-0.0.1.tar.gz` (Source Archive / sdist)
2. `campaign_logger-0.0.1-py3-none-any.whl` (Built Distribution / wheel)

---

## Step 4: Verify the Build

Before uploading, it is a best practice to check if the generated files have any formatting or metadata errors (such as a broken `README.rst`).

Run:

```bash
twine check dist/*
```

You should see an output similar to: `Checking dist/campaign_logger-0.0.1-py3-none-any.whl: PASSED`. If you see errors, they must be fixed before uploading.

---

## Step 5: (Optional) Upload to TestPyPI

If you want to practice to ensure everything looks good on the website before making it official:

```bash
twine upload --repository testpypi dist/*
```

- **Username:** When prompted, type exactly `__token__` (that is two underscores, the word "token", and two underscores).
- **Password:** Paste the API token you generated on **TestPyPI** (starting with `pypi-`).

You can then view your package at `https://test.pypi.org/project/campaign-logger/`.

---

## Step 6: Upload to Official PyPI

When you are ready to publish the package to the real world, run:

```bash
twine upload dist/*
```

- **Username:** Type exactly `__token__`
- **Password:** Paste your official **PyPI** API token.

You will see an upload progress bar. Once finished, congratulations! Your package is live.

---

## Step 7: Verify the Upload

Wait a minute or two, and then try installing your package from anywhere on your computer (outside of the project folder):

```bash
pip install campaign-logger
```

If it installs successfully, you're officially published! You can view your package page at `https://pypi.org/project/campaign-logger/`.

---

## Updating the Package in the Future

When you make changes to the code in the future and want to release a new version:

1. Update the `version="0.0.1"` number in `setup.py` to a higher number (e.g., `"0.0.2"`).
2. Delete the old files inside the `dist/` directory to avoid uploading them again.
3. Repeat **Step 3** (`python -m build`) and **Step 6** (`twine upload dist/*`).