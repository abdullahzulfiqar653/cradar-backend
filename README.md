# cradar.ai

## Dependencies

For opening and saving non-wav files – like mp3 – you'll need ffmpeg or libav.

# To build and run

## In local

1. Install necessary packages, such as:
   - pipenv
   - mysql client
   - ffmpeg
2. Have the postgres database connection ready
3. Have the redis connection ready
4. Copy the content of .env.example to .env
5. Replace the following fields:
   - `OPENAI_API_KEY`
   - `GOOGLE_APPLICATION_CREDENTIALS`
   - `MASTER_DB_*`
   - `CELERY_BROKER_URL`
   - `EMAIL_HOST_USER` - Use gmail account
   - `EMAIL_HOST_PASSWORD` - **NOT** gmail account password. Please follow the [guideline](https://support.google.com/mail/answer/185833?hl=en) to create the app password and add it here.
6. Install the python dependencies - `pipenv install`
7. Go into the python virtual environment - `pipenv shell`
8. Migrate the database - `python manage.py migrate`
9. Start the server - `python manage.py runserver`
10. Start the celery beat for scheduled tasks - `celery -A cradarai beat`
11. Start the celery worker for scheduled and async tasks - `celery -A cradarai worker`

## Using local docker

```shell
docker compose --profile local up
```

This `local` profile will run frontend, nginx and db also.

# Adding new python packages

1. Determine if the new package is only for local or need to push to server
   1. For local only, run `pipenv install --dev <package-name>`
   2. To install in server, run `pipenv install <package-name>`
2. Check Pipfile to see if the installation is as per intended.
3. Fix the package version if possible to avoid version drift.
4. Generate the requirements.txt file `pipenv requirements > requirements.txt`

Note: In the server, python packages are installed from requirements.txt file rather than the pipenv because the versions are still drifting everytime we run `pipenv install`. So the step to generate the requirements.txt is really important for the server to install the new package.

# Celery

The cronjob is defined in cradarai/celery.py.

1. To run celery worker:

   ```shell
   celery -A cradarai worker
   ```

   Restart the celery worker if the celery task functions are updated.

2. To run celery beat (the process to queue the cronjob):

   ```shell
   celery -A cradarai beat
   ```

   Restart the celery beat if the schedules are updated.

3. To run flower to monitor the celery workers:
   ```shell
   celery -A cradarai flower
   ```
   After that, go to localhost:5555.

# Known issues

1. If you are using MacOS and encounter this issue when running celery
   ```
   objc[88793]: +[__NSCFConstantString initialize] may have been in progress in another thread when fork() was called.
   objc[88793]: +[__NSCFConstantString initialize] may have been in progress in another thread when fork() was called. We cannot safely call it or ignore it in the fork() child process. Crashing instead. Set a breakpoint on objc_initializeAfterForkError to debug.
   ```
   Please run this before set this env var
   `export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES`

# Code practices

1. Use model - serializer - view approach. So that we have consistent schema, and we can render the schema in swagger.
2. Implement create, update and delete logics in serializers, not views.
3. Handle request errors by raising `rest_framework.exceptions`. Do not return a 4xx response directly. This is for consistency, so that we have the same format for the json response.
4. When adding new environment variable, add it in .env.example, and read it into [settings.py](cradarai/settings.py). Do not read environment variables directly from other parts of the code, so that we keep track of all the environment variables that affect the apps.
5. Use [`InProjectOrWorkspace` permission](api/permissions.py?plain=1#L13) to authorize the access of the resource referred by the first id in the url. See the following example for more details:
   - In the following url `/api/projects/{project_id}/reports/`, the first (and only) id in the url is `project_id`.
   - Check if user has the permission to access the resource (project in this case).
   - If the user has the right access, attach the resource to the `request`.
   - In the serializers and views, access the resource from the `request` to reduce the number of queries.

# Google Drive Integration Documentation

## Steps for local testing

1. Setup for Google Console:
   - Go to Google Cloud web interface to access the API & Services page for Raijin: https://console.cloud.google.com/apis/credentials/oauthclient/
   - Go to the Credentials tab. You should see "Raijin Google Login" as the Name.
   - Set Authorized JavaScript Origins URL as frontend localhost domain, for e.g. `http://localhost:5173`
   - Set Authorized redirect URIs as `{frontend localhost domain}/googledrive/redirect`
   - Save changes
2. Runserver on backend and start frontend to login to Raijin web app.
3. Find "Connect to Google Drive" button on header component. Click to kickstart OAuth process.
4. "Connect to Google Drive" button will bring you to Google OAuth page. Choose Google account you want to connect Raijin account to and click "continue".
5. After successful authorization, the page will automatically redirect to frontend redirect page, which will show a success message popup.
6. Page will automatically redirect back to Raijin account after success message popup is displayed.
7. Open Create Knowledge Source Dialog on frontend page and click on the Google Drive input component.
8. Check that Google Drive files are accessed and displayed in the dropdown.
9. Select Google Drive file to create Knowledge Source with and click "continue".
10. Once Knowledge Source is created, check that the Knowledge Source has the correct file attached to it.
