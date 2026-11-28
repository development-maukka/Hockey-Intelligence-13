# Development and verification

Requires Python 3.12 and Node.js for the JavaScript syntax check.

```sh
python -m pip install 'groq>=0.30,<2' 'beautifulsoup4>=4.12,<5' 'sportsdataverse==0.2.0b1'
python -m unittest discover -s tests
node --check site/app.js
node --check site/install.js
npm install --no-save --package-lock=false jsdom@26
node --test tests/test_install.cjs
python update.py
python -m http.server 8000 --directory site
```

The optional GROQ_API_KEY must be supplied through the environment; it is not included in this archive. Without it, statistical views still work and AI briefing generation is skipped. The generated site/data.json is fetched content, not source. Deploy the site directory after approval. Version 0.5.3 includes the three latest public versions in Info.
