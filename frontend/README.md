# AI Bet Analysis — Telegram Mini App (Frontend)

This directory contains the React 19 + TypeScript + Vite project for the Telegram Mini App.

## Technical Stack
- **React 19** & **TypeScript**
- **Tailwind CSS v3** (Midnight Luxe design system)
- **GSAP** (Smooth entrance animations)
- **Lucide Icons**

## Local Development Setup

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Configure API Base Url**
   By default, local API requests are sent to `/api` proxying relative paths. Ensure your backend is running.
   If you want to configure custom proxy configuration, edit `vite.config.ts`.

3. **Start Development Server**
   ```bash
   npm run dev
   ```

## Testing inside Telegram (Using Ngrok)

To test the WebApp interface natively inside the Telegram client:
1. Start the local Vite server (normally runs on `http://localhost:5173`).
2. Start ngrok tunnel pointing to your Vite server port:
   ```bash
   ngrok http 5173
   ```
3. Copy the secure HTTPS URL from ngrok (e.g. `https://xxxx.ngrok-free.app`).
4. Go to Telegram BotFather, select your bot, and edit the WebApp URL or setup a menu button pointing to this ngrok URL.
5. Alternatively, open the link directly inside Telegram.

## Production Build

Build the static package using:
```bash
npm run build
```
The output files will be compiled into `dist/` directory ready for Nginx deployment.
