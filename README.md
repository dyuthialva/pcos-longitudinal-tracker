# PCOS Longitudinal Tracker

A clinician-facing prototype for reviewing **longitudinal PCOS patient data** across visits, trends, meaningful changes, attention areas, and supporting evidence.

> **Prototype • Synthetic Data • Decision Support Only**
> This application is not a diagnostic tool.

## What it includes

* Clinician authentication with protected routes
* Session persistence and idle-session timeout
* Failed-login rate limiting and temporary lockout
* Patient worklist with search and attention-based sorting
* Patient overview with Attention Map and clinical reasoning
* Longitudinal visit comparison and meaningful changes
* "What Changed Most" summary
* Parameter trends across visits
* Evidence and observation views
* Responsive clinician dashboard
* Mock clinical API with a future FastAPI integration path
* Basic frontend security headers and session/data handling

## Tech Stack

* **React**
* **TypeScript**
* **Vite**
* **Tailwind CSS**
* **React Router**
* **Context API**
* **Lucide React**

## Architecture

The frontend currently uses a **mock clinical API** with synthetic patients and demo clinician accounts.

The API layer is separated through `clinicalApi.ts`, allowing the application to switch to a FastAPI backend later using:

```env
VITE_API_BASE_URL=
```

When the variable is empty, the application uses the local mock API.

## Run Locally

```bash
npm install
npm run dev
```

Build for production:

```bash
npm run build
```

### Demo Login

```text
Email: dr.mehta@clinic.local
Password: ClinicianDemo!2026
```

## Project Status

This is a **development prototype using synthetic data**. It is designed to demonstrate longitudinal clinical decision-support workflows and is not intended for diagnosis or production clinical use.
