# ArtForge Publisher

A local-first AI-powered art publishing assistant that helps digital artists analyze artwork and generate platform-specific social media content using local vision models.

## Features

- **Local-First AI**: All image analysis runs locally using LM Studio and Qwen2.5-VL-7B
- **Vision Analysis**: Extract metadata, style information, and artistic insights from artwork
- **Platform-Specific Content**: Generate optimized posts for ArtStation, X, Instagram, Reddit, and DeviantArt
- **Prompt Versioning**: Edit and version prompt templates without touching code
- **Human Approval**: Review and edit all generated content before publishing
- **Modular Architecture**: Clean separation of concerns with service-oriented design

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React/TS)                     │
│  Image Upload | Analysis Display | Content Editor | Prompts  │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────┴────────────────────────────────┐
│                  Backend (FastAPI)                          │
│  API Layer | Service Layer | Data Layer | LM Studio Client  │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                  Data Layer (SQLite)                        │
│  Images | Analysis | Content | Prompt Versions             │
└─────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────┐
│                  LM Studio (Local)                           │
│              Qwen2.5-VL-7B-Instruct                          │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- LM Studio with Qwen2.5-VL-7B-Instruct model loaded
- Git

## Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` to configure your settings:
```env
LM_STUDIO_ENDPOINT=http://localhost:1234/v1/chat/completions
LM_STUDIO_MODEL=Qwen2.5-VL-7B-Instruct
```

5. Initialize the database:
```bash
python -c "from app.core.database import init_db; init_db()"
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Running the Application

### Start LM Studio

1. Open LM Studio
2. Load the Qwen2.5-VL-7B-Instruct model
3. Start the server (default: http://localhost:1234)
4. Enable the OpenAI-compatible API

### Start Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000
API documentation: http://localhost:8000/api/docs

### Start Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at http://localhost:5173

## Usage

### 1. Upload Artwork

- Drag and drop an image or click to select
- Supported formats: JPEG, PNG, WebP, BMP, TIFF
- Maximum file size: 50MB

### 2. Analyze Image

- Click "Analyze Image" to send to LM Studio
- Qwen2.5-VL-7B will extract:
  - Title, subject, environment
  - Art style, color palette, mood
  - Technical details, artistic influences
  - Search keywords, audience interests

### 3. Generate Content

- Click "Generate Content" to create platform-specific posts
- Content is generated for:
  - ArtStation (title, description, tags)
  - X (short, medium, engagement versions)
  - Instagram (hook, body, hashtags)
  - Reddit (titles, body, subreddit recommendations)
  - DeviantArt (title, description, tags)

### 4. Edit and Review

- All content can be manually edited
- Copy content to clipboard
- Mark content as manually edited

### 5. Manage Prompts

- Navigate to "Prompts" tab
- View and edit prompt templates
- Reload prompts from files
- Save new versions
- Set active versions

## Project Structure

```
artforge-publisher/
├── backend/
│   ├── app/
│   │   ├── api/              # API routes and schemas
│   │   ├── core/             # Configuration and database
│   │   ├── models/           # SQLAlchemy models
│   │   ├── repositories/     # Data access layer
│   │   ├── services/         # Business logic
│   │   └── utils/            # Utilities
│   ├── prompts/              # Prompt template files
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API client
│   │   └── types/            # TypeScript types
│   ├── package.json
│   └── vite.config.ts
├── storage/
│   ├── images/               # Uploaded artwork
│   └── thumbnails/           # Generated thumbnails
└── docs/                     # Documentation
```

## API Endpoints

### Images
- `POST /api/v1/images/upload` - Upload image
- `GET /api/v1/images/{id}` - Get image
- `GET /api/v1/images` - List images
- `DELETE /api/v1/images/{id}` - Delete image

### Analysis
- `POST /api/v1/analysis/analyze` - Analyze image
- `GET /api/v1/analysis/{image_id}` - Get analysis
- `PUT /api/v1/analysis/{image_id}` - Update analysis

### Content
- `POST /api/v1/content/generate` - Generate content
- `GET /api/v1/content/{image_id}` - Get all content
- `PUT /api/v1/content/{content_id}` - Update content

### Prompts
- `GET /api/v1/prompts` - List prompts
- `GET /api/v1/prompts/{name}` - Get prompt
- `PUT /api/v1/prompts/{name}` - Update prompt
- `POST /api/v1/prompts/reload` - Reload from file

## Configuration

Key environment variables:

- `LM_STUDIO_ENDPOINT`: LM Studio API endpoint
- `LM_STUDIO_MODEL`: Model name to use
- `DATABASE_URL`: Database connection string
- `MAX_IMAGE_SIZE_MB`: Maximum upload size
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

## Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/
```

### Frontend Development

```bash
cd frontend
npm run dev
npm run build
npm run lint
```

### Code Style

- Backend: Black, Ruff
- Frontend: ESLint, Prettier

## Troubleshooting

### LM Studio Connection Issues

- Ensure LM Studio is running
- Check the endpoint URL in `.env`
- Verify the model is loaded
- Check LM Studio server logs

### Database Issues

- Delete `artforge.db` and reinitialize
- Check file permissions on storage directory

### Frontend Build Issues

- Delete `node_modules` and reinstall
- Clear Vite cache: `rm -rf .vite`

## Future Enhancements

- Phase 2: Publishing integrations (ArtStation, X, DeviantArt)
- Phase 3: Additional platforms (Bluesky, Mastodon, Reddit)
- Analytics tracking and learning system
- Artist style profiles
- Scheduled posting
- A/B testing for prompts

## License

MIT License - feel free to use this project for your own art publishing workflow.

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting PRs.

## Support

For issues and questions, please open an issue on the project repository.
