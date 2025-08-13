const express = require('express');
const axios = require('axios');
const cors = require('cors');

require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

const POSTMARK_API_KEY = process.env.POSTMARK_API_KEY;

app.post('/send-mail', async (req, res) => {
  const { to, subject, body, from } = req.body || {};
  if (!to || !subject || !body) {
    return res.status(400).json({ error: 'Champs to, subject, body obligatoires' });
  }
  if (!POSTMARK_API_KEY) {
    return res.status(500).json({ error: 'Clé API Postmark non configurée' });
  }

  try {
    const response = await axios.post('https://api.postmarkapp.com/email', {
      From: from || process.env.DEFAULT_FROM || 'no-reply@example.com',
      To: to,
      Subject: subject,
      TextBody: body
    }, {
      headers: {
        'X-Postmark-Server-Token': POSTMARK_API_KEY,
        'Content-Type': 'application/json'
      }
    });

    res.status(response.status).json({ status: 'envoyé' });
  } catch (err) {
    console.error('Erreur Postmark:', err.response?.data || err.message);
    res.status(err.response?.status || 500).json({ error: err.response?.data || err.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Proxy Postmark lancé sur le port ${PORT}`));
