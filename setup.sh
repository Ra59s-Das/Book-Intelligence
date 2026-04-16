#!/bin/bash
# BookIQ — One-click setup script
# Usage: bash setup.sh

set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

echo -e "${GREEN}==============================${NC}"
echo -e "${GREEN}  BookIQ — Project Setup      ${NC}"
echo -e "${GREEN}==============================${NC}\n"

echo -e "${YELLOW}[1/5] Setting up Python virtual environment...${NC}"
cd backend
python3 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}[2/5] Installing Python dependencies...${NC}"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo -e "${YELLOW}[3/5] Setting up .env file...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${RED}  ⚠  .env created. Open backend/.env and set GROQ_API_KEY!${NC}"
else
    echo "  .env already exists, skipping."
fi

echo -e "${YELLOW}[4/5] Running database migrations...${NC}"
python manage.py migrate --run-syncdb
python manage.py createcachetable

cd ..

echo -e "${YELLOW}[5/5] Installing frontend dependencies...${NC}"
cd frontend && npm install --silent && cd ..

echo ""
echo -e "${GREEN}✓ Setup complete!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  NEXT STEPS:"
echo ""
echo "  1. Get your FREE Groq API key:"
echo "     https://console.groq.com → Sign up → API Keys → Create Key"
echo ""
echo "  2. Add your key:"
echo "     Open backend/.env → set GROQ_API_KEY=gsk_..."
echo ""
echo "  3. Terminal 1 — start backend:"
echo "     cd backend && source venv/bin/activate && python manage.py runserver"
echo ""
echo "  4. Terminal 2 — start frontend:"
echo "     cd frontend && npm start"
echo ""
echo "  5. Open http://localhost:3000 → click 'Scrape Books'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
