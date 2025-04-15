# Steps for Deploying React Frontend to Firebase Hosting

**Objective:** Host the static React application (`react-frontend`) on a publicly accessible URL using Firebase Hosting, ensuring cost-effectiveness and ease of deployment.

**Prerequisites:**

1.  **Google Account:** A Google account is required to use Firebase/GCP.
2.  **Firebase Project:** A Firebase project created via the Firebase Console (e.g., `document-rag-app-381fb`).
3.  **Node.js & npm:** Required for running the React build process and installing the Firebase CLI.
4.  **Firebase CLI Installation:** Install the Firebase Command Line Interface globally:
    ```bash
    # If permission errors occur, use sudo (macOS/Linux)
    sudo npm install -g firebase-tools
    ```
5.  **Firebase CLI Login:** Authenticate the CLI with your Google Account:
    ```bash
    firebase login
    ```

**Deployment Steps:**

1.  **Navigate to Frontend Directory:** Open your terminal and change into the specific directory containing the frontend code:
    ```bash
    cd path/to/document-rag-app/react-frontend
    ```
    *Crucial Step: Ensure you are *inside* the `react-frontend` directory before running `init`.*

2.  **Initialize Firebase Hosting:** Run the initialization command:
    ```bash
    firebase init hosting
    ```
    *   **Select Project:** Choose `Use an existing project` and select the appropriate Firebase project (e.g., `document-rag-app-381fb`) from the list.
    *   **Public Directory:** When prompted `What do you want to use as your public directory?`, enter the name of the directory that contains the *built* React application files. Based on the project setup (using Vite), this was **`dist`**.
    *   **Single-Page App (SPA):** When asked `Configure as a single-page app (rewrite all urls to /index.html)?`, answer **`y`** (Yes). This is necessary for client-side routing (like React Router) to work correctly.
    *   **Automatic Builds (GitHub):** When asked `Set up automatic builds and deploys with GitHub?`, answer **`N`** (No) for this initial manual setup.
    *   **File Creation:** This process creates/updates two files *inside the `react-frontend` directory*:
        *   `.firebaserc`: Maps the directory to the Firebase project alias.
        *   `firebase.json`: Contains the hosting configuration, specifying `"public": "dist"` and the SPA rewrite rule.

3.  **Build the React Application:** Generate the optimized static production files:
    ```bash
    # Still inside the react-frontend directory
    npm run build
    ```
    *   This command executes the `build` script defined in `package.json` (e.g., `tsc -b && vite build`), populating the `dist` directory with `index.html`, JavaScript bundles, CSS files, and other assets.
    *   *Troubleshooting:* Addressed build errors related to unused variables/imports (TypeScript errors like TS6133) and missing optional dependencies (like `terser`).

4.  **Deploy to Firebase Hosting:** Upload the built files from the `dist` directory to Firebase:
    ```bash
    # Still inside the react-frontend directory
    firebase deploy --only hosting
    ```
    *   The `--only hosting` flag ensures only the hosting configuration is deployed.
    *   *Troubleshooting:* Initially encountered an issue where the default Firebase placeholder page was shown instead of the app. This was because `firebase init` was accidentally run from the root project directory, placing `firebase.json` and `.firebaserc` there. The fix involved moving these two configuration files into the `react-frontend` directory and re-running the deploy command from within `react-frontend`.

**Outcome:**

*   The deployment process uploads the contents of the `react-frontend/dist` directory.
*   Firebase provisions an SSL certificate and makes the site available globally via its CDN.
*   The application is accessible at the **Hosting URL** provided at the end of the deployment (e.g., `https://document-rag-app-381fb.web.app`). 