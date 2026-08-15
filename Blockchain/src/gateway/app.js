'use strict';

const express = require('express');
const routes = require('./routes');
require('dotenv').config();

const app = express();

// Middlewares
app.use(express.json());

// Cargar rutas unificadas con prefijo común
app.use('/api/blockchain', routes);

module.exports = app;
