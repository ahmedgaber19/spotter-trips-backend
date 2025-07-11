# Spotter Backend - Django REST API

Django REST API for the Spotter trucking route planner application.

## Features

- Route calculation using OpenRouteService API
- ELD (Electronic Logging Device) log generation
- HOS (Hours of Service) compliance checking
- Fuel stop recommendations
- REST API endpoints for frontend integration

## Tech Stack

- Django 5.2.4
- Django REST Framework
- OpenRouteService API integration
- No database required (stateless API)

## API Endpoints

- `POST /api/calculate-route/` - Calculate route with stops and ELD logs
- `POST /api/validate-locations/` - Validate location addresses
- `GET /api/health/` - Health check endpoint

## Environment Variables

- `OPENROUTESERVICE_API_KEY` - Your OpenRouteService API key
- `DJANGO_SECRET_KEY` - Django secret key for production
- `DEBUG` - Set to `false` for production

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python manage.py runserver
```

## Deployment

This backend is configured for Vercel deployment:

```bash
vercel --prod
```

See the main project documentation for complete deployment instructions.

## Live API

- **Production**: [Your Vercel URL will go here]
- **Health Check**: [Your Vercel URL]/api/health/

## License

MIT License
