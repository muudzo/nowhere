# Nowhere

**Nowhere** is a real-time, location-scoped, ephemeral "third place" utility. It helps you find and join spontaneous gatherings without social pressure.

## Philosophy
- **Time-bound**: Everything expires. Nothing is permanent.
- **Density over Engagement**: We show you what is happening nearby, now. We don't want you doom-scrolling.
- **Honesty**: No social graph, no influencers, no likes. Just intents and people.
- **Empty State**: If nothing is happening, START SOMETHING.

## Mental Model
1. **Intents**: A declaration of "I am here doing X". Expires in 24 hours.
2. **Joins**: "I'm in". Expires with the intent.
3. **Messages**: Temporary chat for coordination. Expires with the intent.
4. **Identity**: Anonymous, device-scoped. We don't want your email.

## Tech Stack
- **Backend**: FastAPI (Python), Redis (primary store + geo index).
- **Frontend**: React Native (Expo).

## How to Run

### Backend
1. `cd backend`
2. `python3 -m venv venv`
3. `source venv/bin/activate`
4. `pip install -r requirements.txt`
5. `redis-server` (Make sure Redis is running)
6. `uvicorn main:app --reload`

### App
1. `cd app`
2. `npm install`
3. `npm start` (or `npx expo start`)

## License
Unlicensed / Private.
