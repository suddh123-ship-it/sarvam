# Deploying to Render

This app replaces the local ngrok tunnel with a public Render URL. Twilio then
points its webhooks at your Render service.

## 1. Deploy the app

1. Push this repo to GitHub (already done).
2. In [Render](https://dashboard.render.com), click **New +** → **Blueprint**.
3. Select this repo. Render reads [`render.yaml`](render.yaml) and creates the
   web service automatically.
4. When prompted, paste your secrets (these are **not** in the repo):
   - `SARVAM_API_KEY`
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_PHONE_NUMBER`
5. Click **Apply**. Render builds and gives you a public URL like
   `https://sarvam-auto-dealership-bot.onrender.com`.

## 2. Point Twilio at Render

In the [Twilio Console](https://console.twilio.com) → your phone number →
**Voice Configuration**:

- **A call comes in** → Webhook →
  `https://<your-app>.onrender.com/voice/inbound` (HTTP POST)
- **Call status changes** (optional) →
  `https://<your-app>.onrender.com/voice/status` (HTTP POST)

## 3. Verify

- Health check: `https://<your-app>.onrender.com/`
- Dashboard: `https://<your-app>.onrender.com/dashboard`
- Call your Twilio number and speak — the call flows through Sarvam and shows up
  on the dashboard.

## Notes

- **Free plan** spins down after inactivity; the first call after idle has a
  cold-start delay of ~30–60s. Upgrade the plan to keep it warm.
- Generated TTS audio is written to the container's temp dir (ephemeral) and
  served back to Twilio during the call — no persistent storage needed.
- To change secrets later: Render dashboard → your service → **Environment**.
