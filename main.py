#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E. COLI GPT - Enhanced Production Server
With slider, progress bar, and results table
"""
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from datetime import datetime
import json
import csv
import asyncio

from pipeline import ScientificPubMedEColiExtractor

app = FastAPI(
    title="E. coli GPT API",
    description="Mining Literature for Strain Performance Prediction",
    version="2.0.0"
)

# Enable CORS
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced HTML homepage with slider and progress bar
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>E. coli GPT </title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --bg-1: #081627;
            --bg-2: #102d40;
            --bg-3: #f7f9f5;
            --surface: #fdfdfb;
            --surface-alt: #eff4ee;
            --ink: #1d2d35;
            --muted: #53656f;
            --brand: #0b7a75;
            --brand-deep: #055a5f;
            --accent: #e88d2e;
            --danger: #c53d2c;
            --border: #d6e0db;
            --shadow: 0 20px 45px rgba(8, 22, 39, 0.18);
            --radius-lg: 22px;
            --radius-md: 14px;
            --radius-sm: 10px;
        }
        * {
            box-sizing: border-box;
        }
        body {
            font-family: "Space Grotesk", "Trebuchet MS", sans-serif;
            margin: 0;
            padding: 24px;
            color: var(--ink);
            background:
                radial-gradient(circle at 15% 10%, #194860 0%, transparent 36%),
                radial-gradient(circle at 85% 90%, #d57c2c 0%, transparent 26%),
                linear-gradient(160deg, var(--bg-1) 0%, var(--bg-2) 42%, var(--bg-3) 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1160px;
            margin: 0 auto;
            padding: 32px;
            border-radius: 28px;
            background: rgba(251, 253, 250, 0.92);
            border: 1px solid rgba(214, 224, 219, 0.85);
            backdrop-filter: blur(6px);
            box-shadow: var(--shadow);
        }
        .header {
            text-align: left;
            color: #f3faf8;
            padding: 2.3rem;
            border-radius: var(--radius-lg);
            margin-bottom: 2rem;
            background: linear-gradient(140deg, #06344a 0%, #0b7a75 58%, #ef9c42 100%);
            position: relative;
            overflow: hidden;
        }
        .header::after {
            content: "";
            position: absolute;
            width: 260px;
            height: 260px;
            right: -80px;
            top: -110px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.15);
        }
        .header h1 {
            margin: 0;
            font-size: clamp(1.9rem, 2.8vw, 2.8rem);
            letter-spacing: 0.02em;
            position: relative;
            z-index: 1;
        }
        .header p {
            margin: 0.55rem 0 0;
            font-size: 1.02rem;
            opacity: 0.95;
            position: relative;
            z-index: 1;
        }
        .metrics-grid {
            display: grid;
            gap: 14px;
            margin: 28px 0;
            grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        }
        .metric {
            background: linear-gradient(175deg, #ffffff 0%, #eef4ef 100%);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            text-align: center;
            padding: 16px 14px;
            box-shadow: 0 8px 24px rgba(11, 122, 117, 0.09);
        }
        .metric-value {
            font-size: 1.85rem;
            font-weight: 800;
            color: var(--brand);
            margin: 6px 0;
        }
        .metric-label {
            color: var(--muted);
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.15em;
        }
        .card {
            margin: 22px 0;
            padding: 24px;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border);
            background: linear-gradient(180deg, #ffffff 0%, #f3f7f4 100%);
            box-shadow: 0 15px 34px rgba(17, 36, 47, 0.08);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 18px 38px rgba(17, 36, 47, 0.12);
        }
        h2, h3, h4 {
            margin-top: 0;
        }
        .btn {
            border: none;
            cursor: pointer;
            padding: 11px 20px;
            margin: 6px 6px 6px 0;
            border-radius: 999px;
            font-weight: 700;
            font-size: 0.93rem;
            color: #f7fffd;
            background: linear-gradient(130deg, var(--brand) 0%, var(--brand-deep) 100%);
            box-shadow: 0 8px 20px rgba(11, 122, 117, 0.3);
            transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
        }
        .btn:hover {
            transform: translateY(-1px);
            filter: brightness(1.02);
            box-shadow: 0 12px 24px rgba(11, 122, 117, 0.35);
        }
        .btn-secondary {
            background: linear-gradient(130deg, #d57622 0%, #a95a1c 100%);
            box-shadow: 0 8px 20px rgba(169, 90, 28, 0.32);
        }
        #output {
            margin-top: 24px;
            min-height: 210px;
            color: #e8f5f2;
            border-radius: var(--radius-lg);
            padding: 26px;
            background:
                linear-gradient(165deg, rgba(15, 44, 59, 0.98) 0%, rgba(11, 95, 96, 0.97) 55%, rgba(11, 122, 117, 0.96) 100%);
            border: 1px solid rgba(255, 255, 255, 0.22);
            box-shadow: 0 18px 34px rgba(5, 18, 26, 0.35);
        }
        #output p, #output h3, #output h4 {
            color: inherit;
        }
        .slider-container {
            margin: 18px 0;
            padding: 18px;
            border-radius: var(--radius-md);
            border: 1px dashed #9ab4ab;
            background: linear-gradient(180deg, #f8fbf7 0%, #edf3ee 100%);
        }
        .slider {
            width: 100%;
            height: 11px;
            margin: 14px 0;
            border-radius: 999px;
            outline: none;
            appearance: none;
            background: linear-gradient(90deg, rgba(11, 122, 117, 0.3), rgba(232, 141, 46, 0.4));
        }
        .slider::-webkit-slider-thumb {
            appearance: none;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border: 2px solid #eaf4f2;
            background: linear-gradient(135deg, var(--brand) 0%, #14758a 100%);
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
            cursor: pointer;
        }
        .slider-value {
            margin: 8px 0;
            text-align: center;
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--brand-deep);
        }
        .slider-scale {
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
            color: var(--muted);
            font-size: 0.9rem;
        }
        .paper-input-container {
            margin: 18px 0;
        }
        .paper-input-container label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: var(--ink);
        }
        .paper-input {
            width: 100%;
            max-width: 200px;
            padding: 12px 16px;
            font-size: 1rem;
            border: 2px solid var(--border);
            border-radius: var(--radius-md);
            background: #fff;
        }
        .progress-container {
            height: 14px;
            margin: 20px 0 4px;
            border-radius: 999px;
            overflow: hidden;
            display: none;
            background: rgba(6, 52, 74, 0.16);
            border: 1px solid rgba(6, 52, 74, 0.2);
        }
        .progress-bar {
            width: 0%;
            height: 100%;
            background: linear-gradient(90deg, #0b7a75, #ef9c42);
            transition: width 0.25s ease;
        }
        .step-progress {
            margin: 20px 0;
            display: none;
        }
        .step-row {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 14px;
            margin: 6px 0;
            border-radius: var(--radius-sm);
            background: rgba(11, 122, 117, 0.08);
            border: 1px solid rgba(11, 122, 117, 0.15);
            font-size: 0.9rem;
            color: var(--ink);
            transition: all 0.3s ease;
        }
        .step-row.active {
            background: rgba(11, 122, 117, 0.18);
            border-color: var(--brand);
            font-weight: 600;
        }
        .step-row.done {
            background: rgba(29, 139, 92, 0.1);
            border-color: #1d8b5c;
            color: #1d8b5c;
        }
        .step-row.waiting {
            opacity: 0.4;
        }
        .step-icon {
            font-size: 1.1rem;
            min-width: 24px;
            text-align: center;
        }
        .question-input {
            width: 100%;
            margin: 10px 0;
            padding: 14px;
            font-size: 0.97rem;
            border-radius: var(--radius-sm);
            border: 2px solid #c5d4cb;
            background: #fbfefb;
            color: var(--ink);
        }
        .question-input:focus {
            outline: none;
            border-color: var(--brand);
            box-shadow: 0 0 0 3px rgba(11, 122, 117, 0.17);
        }
        table {
            width: 100%;
            margin: 20px 0;
            border-collapse: collapse;
            border-radius: 12px;
            overflow: hidden;
            background: #ffffff;
            box-shadow: 0 8px 18px rgba(6, 37, 44, 0.16);
        }
        th {
            text-align: left;
            padding: 13px 14px;
            color: #f7fffd;
            background: linear-gradient(120deg, #055a5f 0%, #0b7a75 100%);
        }
        td {
            padding: 11px 14px;
            border-bottom: 1px solid #ecf1ee;
            color: #1d2d35;
        }
        tr:hover {
            background: #f4f9f6;
        }
        .api-section {
            margin-top: 32px;
            padding: 26px;
            border-radius: var(--radius-lg);
            border: 1px solid #214852;
            background: linear-gradient(180deg, rgba(5, 40, 54, 0.93) 0%, rgba(7, 58, 68, 0.92) 100%);
            color: #ecf8f6;
            box-shadow: 0 14px 30px rgba(4, 22, 31, 0.3);
        }
        .api-section p, .api-section h3, .api-section h4 {
            color: inherit;
        }
        .api-section .card {
            color: var(--ink);
        }
        .api-section .card p,
        .api-section .card h4 {
            color: var(--ink);
        }
        .api-section .card code {
            background: #e3ece8;
            color: #12333a;
        }
        code {
            padding: 2px 7px;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.14);
            color: #f4fffd;
            font-family: "Consolas", monospace;
        }
        .strain-badge {
            display: inline-block;
            margin: 5px 7px 5px 0;
            padding: 7px 14px;
            border-radius: 999px;
            font-size: 0.82rem;
            cursor: pointer;
            color: #f3fbf8;
            background: linear-gradient(120deg, #0f6670 0%, #0b7a75 100%);
            border: 1px solid rgba(255, 255, 255, 0.22);
            box-shadow: 0 6px 12px rgba(7, 62, 71, 0.25);
            transition: transform 0.15s ease;
        }
        .strain-badge:hover {
            transform: translateY(-1px);
        }
        .chat-bubble {
            max-width: 85%;
            margin: 10px 0;
            padding: 14px 18px;
            border-radius: 18px;
            background: #e4f0ed;
            color: #1f3237;
            border: 1px solid #b9d0c8;
        }
        .chat-bubble.ai {
            margin-left: 22px;
            background: #f2e9da;
            border-color: #ddc7a6;
        }
        .spinner {
            width: 40px;
            height: 40px;
            margin: 20px auto;
            border-radius: 50%;
            border: 4px solid rgba(226, 240, 236, 0.45);
            border-top-color: #ef9c42;
            animation: spin 0.9s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @media (max-width: 768px) {
            body {
                padding: 14px;
            }
            .container {
                padding: 18px;
                border-radius: 20px;
            }
            .card, #output, .api-section {
                padding: 18px;
            }
            .metrics-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>E. coli GPT</h1>
            <p>Mining Literature for Strain Performance</p>
        </div>
        
        <!-- METRICS SECTION -->
        <div class="metrics-grid">
            <div class="metric">
                <div class="metric-value" id="yearRangeLabel" style="font-size: clamp(1rem, 2vw, 1.35rem); line-height: 1.25;">—</div>
                <div class="metric-label">Publication range</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="recordsFound">0</div>
                <div class="metric-label">Records Found</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="tempCoverage">0%</div>
                <div class="metric-label">Temp Data</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="avgConfidence">0%</div>
                <div class="metric-label">Avg Confidence</div>
            </div>
            <div class="metric">
                <div class="metric-value" 
                     id="strainCoverage"
                     style="color: #1d8b5c;">0%</div>
                <div class="metric-label">Strain Coverage</div>
            </div>
        </div>
        
        <!-- PAPER ANALYSIS BY PUBLICATION YEAR -->
        <div class="card">
            <h2> Analyze PubMed Papers</h2>
            <p>Limit extraction by publication year (e.g. from 2020 to present, or 2020 to 2024).</p>
            
            <div class="year-range-row" style="display: flex; flex-wrap: wrap; gap: 16px; align-items: flex-end; margin: 18px 0;">
                <div class="paper-input-container" style="margin: 0;">
                    <label for="yearFrom">From year</label>
                    <input type="number" min="1950" max="2100" value="2020" class="paper-input" id="yearFrom" placeholder="e.g. 2020">
                </div>
                <div class="paper-input-container" style="margin: 0;">
                    <label for="yearTo">To year</label>
                    <input type="number" min="1950" max="2100" value="" class="paper-input" id="yearTo" placeholder="Present (leave empty)">
                </div>
                <div style="padding-bottom: 4px;">
                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; font-weight: 600; color: var(--ink);">
                        <input type="checkbox" id="yearToPresent" checked>
                        To present (current year)
                    </label>
                </div>
            </div>
            <p style="font-size: 0.9rem; color: var(--muted); margin: 0 0 12px;">Uncheck “To present” and set “To year” for a fixed end year (e.g. 2020–2024).</p>
            
            <button class="btn" onclick="analyzePapers()">Analyze PubMed Papers</button>
            
            <div class="progress-container" id="progressContainer">
                <div class="progress-bar" id="progressBar"></div>
            </div>
            <div class="step-progress" id="stepProgress">
                <div class="step-row waiting" id="step1">
                    <span class="step-icon">🔍</span>
                    <span id="step1msg">
                        Step 1/5: Searching PubMed...
                    </span>
                </div>
                <div class="step-row waiting" id="step2">
                    <span class="step-icon">📄</span>
                    <span id="step2msg">
                        Step 2/5: Fetching abstracts...
                    </span>
                </div>
                <div class="step-row waiting" id="step3">
                    <span class="step-icon">📚</span>
                    <span id="step3msg">
                        Step 3/5: PMC full text...
                    </span>
                </div>
                <div class="step-row waiting" id="step4">
                    <span class="step-icon">🔓</span>
                    <span id="step4msg">
                        Step 4/5: Unpaywall open access...
                    </span>
                </div>
                <div class="step-row waiting" id="step5">
                    <span class="step-icon">⚗️</span>
                    <span id="step5msg">
                        Step 5/5: Extracting & validating data...
                    </span>
                </div>
            </div>
        </div>
        
        <!-- QUESTION SECTION -->
        <div class="card">
            <h2> Ask E. coli GPT</h2>
            <input type="text" id="question" placeholder="Ask about strains, yields, temperatures, pH..." class="question-input">
            <button class="btn btn-secondary" onclick="askQuestion()">Ask Question</button>
            
            <div style="margin-top: 15px;">
                <small>Try these questions:</small>
                <div>
                    <span class="strain-badge" onclick="setQuestion('best strain for ethanol?')">best ethanol strain?</span>
                    <span class="strain-badge" onclick="setQuestion('temperature data in abstracts?')">temperature data?</span>
                    <span class="strain-badge" onclick="setQuestion('compare BL21 vs K-12')">BL21 vs K-12</span>
                    <span class="strain-badge" onclick="setQuestion('pH for E. coli fermentation')">optimal pH?</span>
                    <span class="strain-badge" onclick="setQuestion('highest yield strain?')">highest yield?</span>
                </div>
            </div>
        </div>
        
        <!-- RESULTS OUTPUT -->
        <div id="output">
            <h3>Results</h3>
            <p>Run an analysis or ask a question to see results here.</p>
        </div>
        
        <!-- API DOCS SECTION (commented out - uncomment to show)
        <div class="api-section">
            <h3> API Endpoints</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin-top: 20px;">
                <div class="card">
                    <h4><code>GET /health</code></h4>
                    <p>Check server status and information</p>
                    <button class="btn" onclick="testEndpoint('/health')">Test</button>
                </div>
                <div class="card">
                    <h4><code>GET /strains</code></h4>
                    <p>Get all available strain data</p>
                    <button class="btn" onclick="testEndpoint('/strains')">Test</button>
                </div>
                <div class="card">
                    <h4><code>GET /api/analyze</code></h4>
                    <p>Analyze PubMed papers (add ?num_papers=50)</p>
                    <button class="btn" onclick="testEndpoint('/api/analyze?num_papers=10')">Test</button>
                </div>
                <div class="card">
                    <h4><code>POST /api/query</code></h4>
                    <p>Ask questions to E. coli GPT</p>
                    <button class="btn" onclick="showQueryExample()">Example</button>
                </div>
                <div class="card">
                    <h4><code>GET /stats</code></h4>
                    <p>Get server statistics</p>
                    <button class="btn" onclick="testEndpoint('/stats')">Test</button>
                </div>
                <div class="card">
                    <h4><code>GET /docs</code></h4>
                    <p>Interactive API documentation</p>
                    <button class="btn" onclick="window.open('/docs', '_blank')">Open Docs</button>
                </div>
            </div>
        </div>
        -->
    </div>
    
    <script>
        let conversationHistory = [];

        // Slider event listener (commented out - now using input)
        // document.getElementById('paperSlider').addEventListener('input', function() {
        //     document.getElementById('paperValue').textContent = this.value + ' papers';
        // });
        
        function setQuestion(question) {
            document.getElementById('question').value = question;
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            const cb = document.getElementById('yearToPresent');
            const yto = document.getElementById('yearTo');
            function syncYearToDisabled() {
                yto.disabled = cb.checked;
                yto.style.opacity = cb.checked ? '0.5' : '1';
            }
            cb.addEventListener('change', syncYearToDisabled);
            syncYearToDisabled();
        });
        
        async function analyzePapers() {
            const cy = new Date().getFullYear();
            let yf = parseInt(
                document.getElementById('yearFrom').value, 10
            );
            if (isNaN(yf)) yf = 2020;
            yf = Math.max(1950, Math.min(yf, cy));
            const toPresent = document.getElementById(
                'yearToPresent'
            ).checked;
            let yt = cy;
            let rangeLabel = '';
            if (toPresent) {
                rangeLabel = yf + '–present';
            } else {
                yt = parseInt(
                    document.getElementById('yearTo').value, 10
                );
                if (isNaN(yt)) yt = cy;
                yt = Math.max(1950, Math.min(yt, cy));
                if (yt < yf) { const t = yt; yt = yf; yf = t; }
                rangeLabel = yf + '–' + yt;
            }
            let qs = 'year_from=' + encodeURIComponent(yf);
            if (toPresent) qs += '&to_present=1';
            else qs += '&year_to=' + encodeURIComponent(yt);

            const output = document.getElementById('output');
            const progressContainer = document.getElementById(
                'progressContainer'
            );
            const progressBar = document.getElementById(
                'progressBar'
            );
            const stepProgress = document.getElementById(
                'stepProgress'
            );

            output.innerHTML = `
                <div style="text-align: center; padding: 40px;">
                    <div class="spinner"></div>
                    <h3>Fetching papers (${rangeLabel})…</h3>
                    <p style="color:#aaa; font-size:0.9rem;">
                        Searching PubMed, PMC, and Unpaywall.
                        This takes 1–3 minutes.
                    </p>
                </div>
            `;

            progressContainer.style.display = 'block';
            if (stepProgress) {
                stepProgress.style.display = 'block';
                for (let i = 1; i <= 5; i++) {
                    const el = document.getElementById(
                        'step' + i
                    );
                    if (el) el.className = 'step-row waiting';
                }
                const s1 = document.getElementById('step1');
                if (s1) s1.className = 'step-row active';
            }

            let progress = 0;
            const interval = setInterval(() => {
                progress += 3;
                if (progress > 88) progress = 88;
                progressBar.style.width = progress + '%';
                
                if (stepProgress) {
                    const step = Math.floor(progress / 18) + 1;
                    for (let i = 1; i <= 5; i++) {
                        const el = document.getElementById(
                            'step' + i
                        );
                        if (!el) continue;
                        if (i < step) {
                            el.className = 'step-row done';
                        } else if (i === step) {
                            el.className = 'step-row active';
                        } else {
                            el.className = 'step-row waiting';
                        }
                    }
                }
            }, 2000);

            try {
                const response = await fetch(
                    '/api/analyze?' + qs
                );
                const data = await response.json();

                clearInterval(interval);
                progressBar.style.width = '100%';

                if (stepProgress) {
                    for (let i = 1; i <= 5; i++) {
                        const el = document.getElementById(
                            'step' + i
                        );
                        if (el) el.className = 'step-row done';
                    }
                    setTimeout(() => {
                        stepProgress.style.display = 'none';
                    }, 2000);
                }

                setTimeout(() => {
                    progressContainer.style.display = 'none';
                    progressBar.style.width = '0%';
                }, 600);

                const dispRange = 
                    data.publication_range_label || rangeLabel;
                document.getElementById(
                    'yearRangeLabel'
                ).textContent = dispRange;
                document.getElementById(
                    'recordsFound'
                ).textContent = data.records_found || 0;
                document.getElementById(
                    'tempCoverage'
                ).textContent =
                    data.statistics?.temperature_coverage ?? 
                    '0%';
                document.getElementById(
                    'avgConfidence'
                ).textContent =
                    data.statistics?.average_confidence_pct ??
                    data.statistics?.avg_confidence ?? '0%';

                const strainEl = document.getElementById(
                    'strainCoverage'
                );
                if (strainEl) {
                    strainEl.textContent =
                        data.statistics?.strain_coverage_pct ??
                        '0%';
                }

                showAnalysisResults(data);
                window._lastAnalysisComparison =
                    data.comparison || null;

            } catch (error) {
                clearInterval(interval);
                progressContainer.style.display = 'none';
                if (stepProgress) {
                    stepProgress.style.display = 'none';
                }
                output.innerHTML = `
                    <div style="color:#9c261a;
                                background:#ffe7e1;
                                padding:20px;
                                border-radius:10px;
                                border:1px solid #efc2b8;">
                        <h4>Error</h4>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }
        
        function showAnalysisResults(data) {
            // Use statistics from API response
            let tempPercent = data.statistics?.temperature_coverage ?? '0%';
            let phPercent = data.statistics?.ph_coverage ?? '0%';
            let avgConf = data.statistics?.average_confidence_pct ?? data.statistics?.avg_confidence ?? '0%';
            
            let html = `
                <div style="background: #e8f3ef; color: #18313a; padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #b8d1c9;">
                    <h3> Analysis Complete!</h3>
                    <p>Found <strong>${data.records_found}</strong> validated records from PubMed</p>
                    <p><strong>Key Finding:</strong> ${data.statistics.key_finding}</p>
                </div>
                
                <h4> Extracted Data (showing first ${data.results.length} records)</h4>
            `;
            
            if (data.results && data.results.length > 0) {
                html += `
                    <table>
                        <thead>
                            <tr>
                                <th>PMID</th>
                                <th>Source</th>
                                <th>Strain</th>
                                <th>Product</th>
                                <th>Yield</th>
                                <th>Temp</th>
                                <th>pH</th>
                                <th>Medium</th>
                                <th>Confidence</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                data.results.forEach(item => {
                    const pmid = item.PMID ?? '—';
                    const strain = item.strain ?? '—';
                    const product = item.product ?? '—';
                    const yieldVal = item.yield_value ?? 
                                     item.yield ?? '—';
                    const yieldUnit = item.yield_unit 
                        ? ` ${item.yield_unit}` : '';
                    const temp = item.temperature != null 
                        ? item.temperature + '°C' : '—';
                    const ph = item.ph != null 
                        ? item.ph : '—';
                    const medium = item.medium ?? '—';
                    const conf = item.confidence != null 
                        ? item.confidence : 0;
                    
                    const isFulltext = (
                        item.data_source === 'fulltext' || 
                        item.data_source === 'pmc_fulltext'
                    );
                    
                    const sourceBadge = isFulltext
                        ? `<span style="
                            background: #1d8b5c;
                            color: white;
                            padding: 3px 10px;
                            border-radius: 999px;
                            font-size: 0.72rem;
                            font-weight: 700;
                            white-space: nowrap;
                            ">Full Text</span>`
                        : `<span style="
                            background: #7a8a8e;
                            color: white;
                            padding: 3px 10px;
                            border-radius: 999px;
                            font-size: 0.72rem;
                            white-space: nowrap;
                            ">Abstract</span>`;

                    const pmidLink = pmid !== '—'
                        ? `<a href="https://pubmed.ncbi.nlm.nih.gov/${pmid}/" 
                             target="_blank"
                             style="
                                 color: #0b7a75;
                                 text-decoration: none;
                                 font-weight: 700;
                                 font-size: 0.88rem;
                             "
                             title="Open in PubMed">
                             ${pmid} ↗
                           </a>`
                        : '—';

                    html += `
                        <tr>
                            <td>${pmidLink}</td>
                            <td>${sourceBadge}</td>
                            <td><strong>${strain}</strong></td>
                            <td>${product}</td>
                            <td>${yieldVal}${yieldUnit}</td>
                            <td>${temp}</td>
                            <td>${ph}</td>
                            <td>${medium}</td>
                            <td>
                                <div style="
                                    background: #dae5df; 
                                    height: 6px; 
                                    border-radius: 3px; 
                                    overflow: hidden;
                                    margin-bottom: 2px;">
                                    <div style="
                                        height: 100%; 
                                        width: ${conf * 100}%; 
                                        background: #0b7a75;">
                                    </div>
                                </div>
                                <small>${Math.round(conf * 100)}%</small>
                            </td>
                        </tr>
                    `;
                });
                
                html += `
                        </tbody>
                    </table>
                `;
            }
            
            html += `
                <div style="margin-top: 30px;">
                    <h4> Statistics</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div style="background: white; padding: 15px; border-radius: 10px; border-left: 4px solid #0b7a75;">
                            <div style="font-size: 24px; font-weight: bold; color: #0b7a75;">${data.records_found}</div>
                            <div style="color: #666; font-size: 14px;">Records Found</div>
                        </div>
                        <div style="background: white; padding: 15px; border-radius: 10px; border-left: 4px solid #055a5f;">
                            <div style="font-size: 24px; font-weight: bold; color: #055a5f;">${tempPercent}%</div>
                            <div style="color: #666; font-size: 14px;">Temperature Data</div>
                        </div>
                        <div style="background: white; padding: 15px; border-radius: 10px; border-left: 4px solid #e88d2e;">
                            <div style="font-size: 24px; font-weight: bold; color: #e88d2e;">${phPercent}%</div>
                            <div style="color: #666; font-size: 14px;">pH Data</div>
                        </div>
                        <div style="background: white; padding: 15px; border-radius: 10px; border-left: 4px solid #1d8b5c;">
                            <div style="font-size: 24px; font-weight: bold; color: #1d8b5c;">${avgConf}%</div>
                            <div style="color: #666; font-size: 14px;">Avg Confidence</div>
                        </div>
                    </div>
                </div>
                `;
            
            if (data.comparison &&
                (data.comparison.abstract_records > 0 || data.comparison.fulltext_records > 0)) {
                const abs = data.comparison.abstract || {};
                const ft = data.comparison.fulltext || {};
                const absN = data.comparison.abstract_records;
                const ftN = data.comparison.fulltext_records;
                const pmc = data.comparison.pmc_fetch || {};

                html += `
          <div style="margin-top: 30px;">
              <h4>📊 Data Availability: Abstract vs Full Text (Materials &amp; Methods)</h4>
              <p style="color: #53656f; font-size: 0.9rem; margin-bottom: 16px;">
                  This is the core scientific finding — how much more data is available
                  when reading Materials &amp; Methods vs abstract only.
              </p>

              <div style="overflow-x: auto;">
                  <table style="width: 100%; border-collapse: collapse;
                                background: white; border-radius: 12px;
                                overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.1);">
                      <thead>
                          <tr style="background: linear-gradient(120deg, #055a5f, #0b7a75);">
                              <th style="padding: 14px 16px; color: white; text-align: left; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em;">
                                  Parameter
                              </th>
                              <th style="padding: 14px 16px; color: white; text-align: center; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em;">
                                  Abstract Only<br>
                                  <span style="font-weight: 400; font-size: 0.78rem; opacity: 0.85;">
                                      (${absN} records)
                                  </span>
                              </th>
                              <th style="padding: 14px 16px; color: white; text-align: center; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em;">
                                  Full Text PMC<br>
                                  <span style="font-weight: 400; font-size: 0.78rem; opacity: 0.85;">
                                      (${ftN} records)
                                  </span>
                              </th>
                              <th style="padding: 14px 16px; color: white; text-align: center; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em;">
                                  Difference
                              </th>
                          </tr>
                      </thead>
                      <tbody>
                          ${[
                              ['🧬 Strain Name', abs.strain_name, ft.strain_name],
                              ['🌡️ Temperature', abs.temperature, ft.temperature],
                              ['⚗️ pH', abs.ph, ft.ph],
                              ['📈 Yield', abs.yield, ft.yield],
                          ].map(([label, absVal, ftVal], idx) => {
                              const absNum = parseFloat((absVal || '0').replace('%','')) || 0;
                              const ftNum = parseFloat((ftVal || '0').replace('%','')) || 0;
                              const diff = ftNum - absNum;
                              const diffStr = diff >= 0
                                  ? '<span style="color:#1d8b5c;font-weight:700;">+' + diff.toFixed(1) + '%</span>'
                                  : '<span style="color:#c53d2c;font-weight:700;">' + diff.toFixed(1) + '%</span>';
                              const rowBg = idx % 2 === 0 ? '#f9fdfb' : '#ffffff';
                              const barAbsW = Math.round(absNum);
                              const barFtW = Math.round(ftNum);
                              return `<tr style="background: ${rowBg};">
                                      <td style="padding: 14px 16px; font-weight: 600; color: #1d2d35;">
                                          ${label}
                                      </td>
                                      <td style="padding: 14px 16px; text-align: center;">
                                          <div style="font-size: 1.3rem; font-weight: 800; color: #c53d2c;">
                                              ${absVal || '0%'}
                                          </div>
                                          <div style="background: #f0e0de; height: 6px; border-radius: 3px; margin-top: 6px; overflow: hidden;">
                                              <div style="height: 100%; width: ${barAbsW}%; background: #c53d2c; border-radius: 3px;"></div>
                                          </div>
                                      </td>
                                      <td style="padding: 14px 16px; text-align: center;">
                                          <div style="font-size: 1.3rem; font-weight: 800; color: #1d8b5c;">
                                              ${ftVal || 'N/A'}
                                          </div>
                                          <div style="background: #d8ede3; height: 6px; border-radius: 3px; margin-top: 6px; overflow: hidden;">
                                              <div style="height: 100%; width: ${barFtW}%; background: #1d8b5c; border-radius: 3px;"></div>
                                          </div>
                                      </td>
                                      <td style="padding: 14px 16px; text-align: center; font-size: 1rem;">
                                          ${ftN > 0 ? diffStr : '<span style="color:#999;">—</span>'}
                                      </td>
                                  </tr>`;
                          }).join('')}
                      </tbody>
                  </table>
              </div>

              <div style="margin-top: 16px; padding: 16px 20px; background: #f0f7f4;
                          border-radius: 10px; border-left: 4px solid #0b7a75;
                          color: #18313a; font-size: 0.9rem;">
                  <strong>PMC full text fetched:</strong>
                  ${pmc.success || 0} papers successfully,
                  ${pmc.failed || 0} failed,
                  ${pmc.fallback || 0} fell back to abstract.
                  ${ftN === 0
                      ? ' No full-text records in this run — try a broader date range to find more open-access papers on PMC.'
                      : ''}
              </div>
          </div>
      `;
            }

            if (data.year_distribution && 
                Object.keys(data.year_distribution).length > 0) {
                
                const years = Object.keys(data.year_distribution);
                const counts = Object.values(data.year_distribution);
                const maxCount = Math.max(...counts);
                
                html += `
                    <div style="margin-top: 30px;">
                        <h4>📅 Records by Publication Year</h4>
                        <div style="
                            display: flex;
                            align-items: flex-end;
                            gap: 8px;
                            padding: 20px;
                            background: white;
                            border-radius: 12px;
                            border: 1px solid var(--border);
                            min-height: 140px;
                            overflow-x: auto;">
                            ${years.map((yr, i) => {
                                const count = counts[i];
                                const heightPct = Math.max(
                                    8, 
                                    (count / maxCount) * 100
                                );
                                return `
                                    <div style="
                                        display: flex;
                                        flex-direction: column;
                                        align-items: center;
                                        gap: 4px;
                                        min-width: 40px;
                                        flex: 1;">
                                        <div style="
                                            font-size: 0.75rem;
                                            color: #0b7a75;
                                            font-weight: 700;">
                                            ${count}
                                        </div>
                                        <div style="
                                            width: 100%;
                                            height: ${heightPct}px;
                                            background: linear-gradient(
                                                180deg,
                                                #0b7a75,
                                                #055a5f
                                            );
                                            border-radius: 4px 4px 0 0;
                                            min-height: 8px;
                                            transition: height 0.3s ease;">
                                        </div>
                                        <div style="
                                            font-size: 0.72rem;
                                            color: #666;
                                            transform: rotate(-45deg);
                                            white-space: nowrap;
                                            margin-top: 4px;">
                                            ${yr}
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                `;
            }

            html += `
                
                <div style="margin-top: 20px;">
                    <button class="btn" onclick="downloadResults('${data.analysis_id}')">
                         Download JSON Results
                    </button>
                    <button class="btn" 
                            onclick="downloadCSV()"
                            style="background: linear-gradient(
                                130deg, #1d8b5c 0%, #156b47 100%
                            ); 
                            box-shadow: 0 8px 20px 
                            rgba(29, 139, 92, 0.3);">
                        📊 Download CSV
                    </button>
                    <button class="btn btn-secondary" onclick="showDataGaps()">
                         Show Data Gaps Analysis
                    </button>
                </div>
            `;
            
            document.getElementById('output').innerHTML = html;
        }
        
        async function askQuestion() {
            const question = document.getElementById(
                'question'
            ).value;
            if (!question.trim()) {
                alert('Please enter a question');
                return;
            }

            const output = document.getElementById('output');
            output.innerHTML = `
                <div style="text-align: center; padding: 40px;">
                    <div class="spinner"></div>
                    <h3>Thinking...</h3>
                    <p>Processing: "${question}"</p>
                </div>
            `;

            try {
                const response = await fetch('/api/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        question: question,
                        history: conversationHistory
                    })
                });

                const data = await response.json();

                conversationHistory.push({
                    question: question,
                    answer: data.answer
                });
                if (conversationHistory.length > 6) {
                    conversationHistory =
                        conversationHistory.slice(-6);
                }

                let html = '';

                conversationHistory.forEach((ex, idx) => {
                    const isLatest = idx ===
                        conversationHistory.length - 1;
                    const opacity = isLatest ? '1' : '0.65';
                    html += `
                        <div class="chat-bubble"
                             style="background:#dcefeb;
                                    opacity:${opacity};">
                            <strong>You:</strong>
                            ${ex.question}
                        </div>
                        <div class="chat-bubble ai"
                             style="opacity:${opacity};">
                            <div style="
                                display: flex; 
                                justify-content: space-between;
                                align-items: center;
                                margin-bottom: 8px;">
                                <strong>E. coli GPT:</strong>
                                <span style="
                                    font-size: 0.72rem;
                                    padding: 2px 8px;
                                    border-radius: 999px;
                                    background: ${data.gpt2_available && 
                                        data.model_used === 'gpt2_finetuned'
                                        ? 'rgba(11,122,117,0.15)' 
                                        : 'rgba(0,0,0,0.1)'};
                                    color: ${data.gpt2_available && 
                                        data.model_used === 'gpt2_finetuned'
                                        ? '#0b7a75' 
                                        : '#888'};
                                    ">
                                    ${data.gpt2_available && 
                                      data.model_used === 'gpt2_finetuned'
                                        ? '🤖 GPT-2' 
                                        : '📊 Data match'}
                                </span>
                            </div>
                            ${ex.answer.replace(
                                /\\n/g, '<br>'
                            )}
                            ${data.records_used > 0 
                                ? `<div style="
                                    font-size: 0.75rem; 
                                    color: #888; 
                                    margin-top: 8px;
                                    border-top: 1px solid rgba(0,0,0,0.08);
                                    padding-top: 6px;">
                                    Based on ${data.records_used} 
                                    matched records from your analysis
                                   </div>` 
                                : ''}
                        </div>
                    `;
                });

                html += `
                    <div style="text-align:right;
                                margin-top:8px;
                                color:#aaa;
                                font-size:12px;">
                        ${new Date().toLocaleTimeString()}
                        · ${conversationHistory.length}
                        exchange(s) in context
                        ${data.context_strain
                            ? '· Context: ' +
                              data.context_strain
                            : ''}
                    </div>
                `;

                let suggestions = [];

                if (data.context_strain) {
                    suggestions.push([
                        'What temperature does it need?',
                        '🌡️ Temperature?'
                    ]);
                    suggestions.push([
                        'What is its typical yield?',
                        '📈 Yield?'
                    ]);
                    suggestions.push([
                        'What pH is optimal for it?',
                        '⚗️ pH?'
                    ]);
                    suggestions.push([
                        'What medium should I use?',
                        '🧪 Medium?'
                    ]);
                } else {
                    suggestions = [
                        ['best strain for protein?',
                         'Best for protein?'],
                        ['best strain for ethanol?',
                         'Best for ethanol?'],
                        ['compare BL21 vs MG1655',
                         'Compare strains'],
                        ['temperature data in abstracts?',
                         'Data gaps?'],
                    ];
                }

                html += `
                    <div style="margin-top:20px;
                                padding:16px 20px;
                                background:#edf4ef;
                                border-radius:12px;
                                border:1px solid #c8d7cf;
                                color:#18313a;">
                        <div style="font-size:0.82rem;
                                    font-weight:600;
                                    margin-bottom:10px;
                                    color:#53656f;
                                    text-transform:uppercase;
                                    letter-spacing:0.08em;">
                            Follow-up questions
                        </div>
                        <div>
                            ${suggestions.map(([full, label]) =>
                                `<span class="strain-badge"
                                 onclick="setAndAsk('${full}')">${label}</span>`
                            ).join('')}
                            <span class="strain-badge"
                                  onclick="clearChat()"
                                  style="background:linear-gradient(
                                      120deg,#7a4012,#5a2f0d
                                  );">
                                🔄 New topic
                            </span>
                        </div>
                    </div>
                `;

                output.innerHTML = html;

            } catch (error) {
                output.innerHTML = `
                    <div style="color:#9c261a;
                                background:#ffe7e1;
                                padding:20px;
                                border-radius:10px;">
                        <h4>Error</h4>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }

        function setAndAsk(q) {
            document.getElementById('question').value = q;
            askQuestion();
        }

        function clearChat() {
            conversationHistory = [];
            document.getElementById('question').value = '';
            document.getElementById('output').innerHTML = `
                <h3>Results</h3>
                <p style="color:#aaa; font-size:0.9rem;">
                    Conversation cleared. Ask a new question.
                </p>
            `;
        }

        async function testEndpoint(endpoint) {
            const output = document.getElementById('output');
            output.innerHTML = `<div style="text-align: center;"><div class="spinner"></div><p>Testing ${endpoint}...</p></div>`;
            
            try {
                const response = await fetch(endpoint);
                const data = await response.json();
                
                output.innerHTML = `
                    <h3>${endpoint}</h3>
                    <pre style="background: #122b38; color: #f2f8f8; padding: 20px; border-radius: 10px; overflow: auto; max-height: 400px; border: 1px solid #2e5160;">
${JSON.stringify(data, null, 2)}
                    </pre>
                    <button class="btn" onclick="copyToClipboard('${JSON.stringify(data, null, 2).replace(/'/g, "\\'")}')">
                        ?? Copy JSON
                    </button>
                `;
            } catch (error) {
                output.innerHTML = `
                    <div style="color: #9c261a; background: #ffe7e1; padding: 20px; border-radius: 10px; border: 1px solid #efc2b8;">
                        <h4>Error testing ${endpoint}</h4>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }
        
        function showQueryExample() {
            document.getElementById('output').innerHTML = `
                <h3>POST /api/query Example</h3>
                <div style="background: #122b38; color: #f2f8f8; padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid #2e5160;">
                    <h4 style="color: #67c9bf;">Request:</h4>
                    <pre>
POST /api/query
Content-Type: application/json

{
    "question": "best strain for ethanol production?"
}
                    </pre>
                    
                    <h4 style="color: #f0ab57;">Response:</h4>
                    <pre>
{
    "question": "best strain for ethanol production?",
    "answer": "Based on literature:\\n- Protein: BL21(DE3)\\n- Ethanol: FOR strain\\n  Organic acids: MG1655",
    "timestamp": "2024-01-15T10:30:00",
    "confidence": 0.85
}
                    </pre>
                </div>
                
                <button class="btn" onclick="testEndpoint('/api/query')">
                    Test with POST
                </button>
            `;
        }
        
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text);
            alert('Copied to clipboard!');
        }
        
        function downloadResults(analysisId) {
            const data = {
                analysis_id: analysisId,
                title: "E. coli GPT Analysis Results",
                timestamp: new Date().toISOString(),
                server: "http://93.127.214.36:8000/",
                note: "Generated by E. coli GPT - Literature Mining Platform"
            };
            
            const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ecoli_gpt_${analysisId}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        function downloadCSV() {
            // Opens the CSV download endpoint
            const link = document.createElement('a');
            link.href = '/api/download/csv';
            link.download = 'ecoli_gpt_data.csv';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        
        function showDataGaps() {
            // Use real data from last analysis if available
            const lastComparison = window._lastAnalysisComparison;

            if (!lastComparison || lastComparison.abstract_records === 0) {
                // Fall back to hardcoded known findings if no analysis run yet
                document.getElementById('output').innerHTML = `
                    <h3>📉 Data Gaps Analysis</h3>
                    <div style="background: #f9efdd; padding: 20px; border-radius: 12px;
                                border-left: 5px solid #e88d2e; margin: 20px 0; color: #3a2b1c;">
                        <h4 style="color: #b5671f;">Run an analysis first to see real data gaps</h4>
                        <p>Click "Analyze PubMed Papers" above to fetch real data.
                           The comparison table will show actual abstract vs. full text
                           coverage from the papers retrieved.</p>
                    </div>
                `;
                return;
            }

            const abs = lastComparison.abstract || {};
            const ft = lastComparison.fulltext || {};
            const absN = lastComparison.abstract_records;
            const ftN = lastComparison.fulltext_records;

            document.getElementById('output').innerHTML = `
                <h3>📉 Data Gaps Analysis — Real Results</h3>
                <div style="background: #f9efdd; padding: 20px; border-radius: 12px;
                            border-left: 5px solid #e88d2e; margin: 20px 0; color: #3a2b1c;">
                    <h4 style="color: #b5671f;">Core Scientific Finding</h4>
                    <p>Critical fermentation parameters are systematically absent from
                       PubMed abstracts but present in Materials &amp; Methods sections.</p>
                </div>
                <div style="display: grid;
                            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                            gap: 16px; margin: 24px 0;">
                    ${[
                        ['🧬 Strain Name', abs.strain_name, ft.strain_name, '#0b7a75'],
                        ['🌡️ Temperature', abs.temperature, ft.temperature, '#c53d2c'],
                        ['⚗️ pH', abs.ph, ft.ph, '#d57622'],
                        ['📈 Yield', abs.yield, ft.yield, '#1d8b5c'],
                    ].map(([label, absVal, ftVal, color]) => `
                        <div style="background: white; padding: 20px; border-radius: 12px;
                                    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                                    border-top: 4px solid ${color};">
                            <div style="font-weight: 700; margin-bottom: 12px;
                                        color: #1d2d35;">${label}</div>
                            <div style="display: flex; justify-content: space-between;
                                        align-items: center; margin-bottom: 8px;">
                                <span style="font-size: 0.8rem; color: #666;">
                                    Abstract (${absN})
                                </span>
                                <span style="font-size: 1.4rem; font-weight: 800;
                                             color: #c53d2c;">
                                    ${absVal || '0%'}
                                </span>
                            </div>
                            <div style="display: flex; justify-content: space-between;
                                        align-items: center;">
                                <span style="font-size: 0.8rem; color: #666;">
                                    Full Text (${ftN})
                                </span>
                                <span style="font-size: 1.4rem; font-weight: 800;
                                             color: #1d8b5c;">
                                    ${ftN > 0 ? (ftVal || '0%') : 'N/A'}
                                </span>
                            </div>
                        </div>
                    `).join('')}
                </div>
                <div style="background: #e8f3ef; color: #18313a; padding: 16px 20px;
                            border-radius: 10px; border: 1px solid #b8d1c9; font-size: 0.9rem;">
                    Based on ${absN + ftN} real extracted records from PubMed and PMC.
                </div>
            `;
        }
        
        // Initialize
        window.onload = function() {
            console.log('E. coli GPT Enhanced Version loaded');
        };
    </script>
</body>
</html>
"""

# Data models
class QueryRequest(BaseModel):
    question: str
    history: Optional[list] = Field(default_factory=list)

# Store analysis history
analyses = {}

class EColiGPTModel:
    """Singleton loader for fine-tuned GPT-2 model.
    Loads once and reuses to avoid loading on 
    every request."""
    
    _instance = None
    _model = None
    _tokenizer = None
    _loaded = False
    _error = None
    MODEL_PATH = "./ecoli_gpt_simple/final"
    
    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def load(self):
        """Load model from disk. 
        Returns True if successful."""
        if self._loaded:
            return True
        try:
            import os
            if not os.path.exists(self.MODEL_PATH):
                self._error = (
                    "Model not trained yet. "
                    "Run pipeline.py first."
                )
                return False
            
            from transformers import (
                AutoTokenizer,
                AutoModelForCausalLM,
            )
            import torch
            
            self._tokenizer = (
                AutoTokenizer.from_pretrained(
                    self.MODEL_PATH
                )
            )
            self._model = (
                AutoModelForCausalLM.from_pretrained(
                    self.MODEL_PATH
                )
            )
            self._model.eval()
            self._loaded = True
            self._error = None
            return True
            
        except Exception as e:
            self._error = str(e)
            self._loaded = False
            return False
    
    def generate(
        self, 
        prompt: str, 
        max_new_tokens: int = 60
    ) -> str:
        """Generate completion for prompt.
        Returns empty string on failure."""
        if not self._loaded:
            if not self.load():
                return ""
        try:
            import torch
            inputs = self._tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=128,
            )
            with torch.no_grad():
                outputs = self._model.generate(
                    inputs.input_ids,
                    max_new_tokens=max_new_tokens,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=(
                        self._tokenizer.pad_token_id
                    ),
                    repetition_penalty=1.3,
                    no_repeat_ngram_size=3,
                )
            full_text = self._tokenizer.decode(
                outputs[0],
                skip_special_tokens=True,
            )
            # Return only the NEW tokens 
            # (strip the prompt)
            if full_text.startswith(prompt):
                generated = full_text[
                    len(prompt):
                ].strip()
            else:
                generated = full_text.strip()
            return generated
        except Exception:
            return ""
    
    @property
    def is_available(self) -> bool:
        import os
        return os.path.exists(self.MODEL_PATH)
    
    @property
    def error_message(self) -> str:
        return self._error or ""

# Initialize singleton
gpt_model = EColiGPTModel()

def normalize_strain(s: str) -> str:
    """Normalize strain name variants to 
    canonical form so BL21, BL21(DE3), bl21 
    are all treated as the same strain."""
    if not s:
        return None
    s = str(s).upper().strip()
    if "BL21" in s:
        return "BL21"
    if "MG1655" in s:
        return "MG1655"
    if "K-12" in s or "K12" in s:
        return "K-12"
    if "DH5" in s:
        return "DH5α"
    if "W3110" in s:
        return "W3110"
    if "BW25113" in s:
        return "BW25113"
    if "JM109" in s:
        return "JM109"
    if "ROSETTA" in s:
        return "Rosetta"
    if "XL1" in s:
        return "XL1-Blue"
    if "TOP10" in s:
        return "Top10"
    if "DH10B" in s:
        return "DH10B"
    return s


def safe_median(values: list):
    """Return median of a list of numbers.
    More robust than mean for scientific data 
    with outliers."""
    if not values:
        return None
    try:
        vals = sorted(float(v) for v in values)
        n = len(vals)
        if n == 0:
            return None
        if n % 2 == 1:
            return vals[n // 2]
        return (vals[n // 2 - 1] + vals[n // 2]) / 2
    except Exception:
        return None


import re as _re

def tokenize(text: str) -> set:
    """Tokenize text into word set using regex.
    Better than split() for scientific text."""
    return set(
        _re.findall(r'\b\w+\b', str(text).lower())
    )


def retrieve_relevant_records(
    question: str,
    max_records: int = 5
) -> list:
    """Retrieve most relevant records using 
    term overlap similarity.
    Simple and effective for datasets under 500 records.
    No FAISS or neural embeddings needed."""
    
    if not analyses:
        return []
    
    latest_key = sorted(analyses.keys())[-1]
    all_records = analyses[latest_key].get(
        'results', []
    )
    
    if not all_records:
        return []
    
    q_terms = tokenize(question)
    
    # Remove stop words
    stop_words = {
        'what', 'is', 'the', 'a', 'an', 'for',
        'of', 'in', 'to', 'and', 'or', 'how',
        'does', 'do', 'which', 'best', 'good',
        'me', 'tell', 'about', 'give', 'show',
        'can', 'you', 'i', 'we', 'my', 'your',
    }
    q_terms = q_terms - stop_words
    
    if not q_terms:
        # No meaningful terms — return most complete
        def completeness(r):
            return sum(1 for f in [
                r.get('strain'), r.get('temperature'),
                r.get('ph'), r.get('yield_value'),
                r.get('medium'),
            ] if f is not None and f != '')
        return sorted(
            all_records, 
            key=completeness, 
            reverse=True
        )[:max_records]
    
    scored = []
    for r in all_records:
        # Build record text for matching
        record_text = ' '.join(filter(None, [
            str(normalize_strain(r.get('strain')) or ''),
            str(r.get('product') or ''),
            str(r.get('medium') or ''),
            str(r.get('carbon_source') or ''),
            str(r.get('temperature') or ''),
            str(r.get('ph') or ''),
            str(r.get('yield_value') or ''),
        ])).lower()
        
        record_terms = tokenize(record_text)
        
        # Term overlap score
        overlap = len(q_terms & record_terms)
        
        # Bonus for complete records
        completeness = sum(1 for f in [
            r.get('strain'), r.get('temperature'),
            r.get('ph'), r.get('yield_value'),
            r.get('medium'),
        ] if f is not None and f != '')
        
        # Bonus for fulltext records
        is_fulltext = r.get('data_source') in (
            'fulltext', 'pmc_fulltext'
        )
        
        score = (
            overlap * 3 +
            completeness * 0.5 +
            (2 if is_fulltext else 0) +
            (1.5 if r.get('yield_value') else 0) +
            (1.0 if r.get('temperature') else 0) +
            (1.0 if r.get('ph') else 0)
        )
        
        if score > 0:
            scored.append((score, r))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:max_records]]


def get_all_real_data() -> list:
    """Get all records from latest analysis."""
    if not analyses:
        return []
    latest = sorted(analyses.keys())[-1]
    return analyses[latest].get('results', [])


def answer_best_strain(
    records: list, 
    all_data: list,
    product_filter: str = None
) -> str:
    """Find best strain by yield from real data.
    Uses all_data for statistics, records for 
    specific matches."""
    
    # Filter by product if specified
    source = all_data if all_data else records
    if product_filter:
        filtered = [
            r for r in source
            if product_filter.lower() in 
            (r.get('product') or '').lower()
        ]
    else:
        filtered = [
            r for r in source
            if r.get('strain') and r.get('product')
        ]
    
    if not filtered:
        return None
    
    product_clause = (
        f" for {product_filter}" 
        if product_filter else ""
    )
    if len(filtered) < 3:
        return (
            f"Insufficient data{product_clause} — "
            f"only {len(filtered)} record(s) found. "
            f"Try a broader date range or different "
            f"product to get reliable statistics."
        )
    
    # Group by strain, find best yield per strain
    strain_data = {}
    for r in filtered:
        s = normalize_strain(r.get('strain'))
        if not s:
            continue
        y = r.get('yield_value')
        p = r.get('product', '')
        t = r.get('temperature')
        ph = r.get('ph')
        unit = (r.get('yield_unit') or '').strip()
        
        if s not in strain_data:
            strain_data[s] = {
                'gg_yields': [],
                'gl_yields': [],
                'yields': [],
                'products': set(),
                'temps': [],
                'phs': [],
                'count': 0
            }
        
        strain_data[s]['count'] += 1
        strain_data[s]['products'].add(p)
        
        if y:
            try:
                yf = float(y)
                if unit == 'g/g':
                    strain_data[s]['gg_yields'].append(yf)
                elif unit == 'g/L':
                    strain_data[s]['gl_yields'].append(yf)
                else:
                    # Guess unit from value range
                    if yf <= 1.5:
                        strain_data[s]['gg_yields'].append(yf)
                    else:
                        strain_data[s]['gl_yields'].append(yf)
            except Exception:
                pass
        
        if t:
            try:
                strain_data[s]['temps'].append(float(t))
            except Exception:
                pass
        if ph:
            try:
                strain_data[s]['phs'].append(float(ph))
            except Exception:
                pass
    
    if not strain_data:
        return None
    
    # Find strain with highest average yield
    def avg_yield(sd):
        # Prefer g/g yields for ranking
        # Fall back to g/L if no g/g data
        # Never mix units in a single median
        gg = sd.get('gg_yields', [])
        gl = sd.get('gl_yields', [])
        if gg:
            return safe_median(gg) or 0
        elif gl:
            # Scale g/L down so it doesn't 
            # artificially dominate g/g rankings
            med = safe_median(gl) or 0
            return med / 100.0
        return 0
    
    ranked = sorted(
        strain_data.items(),
        key=lambda x: avg_yield(x[1]),
        reverse=True
    )
    
    lines = []
    for strain, sd in ranked[:4]:
        line = f"• {strain}: {sd['count']} papers"
        if sd['yields']:
            avg = avg_yield(sd)
            line += f", avg yield {avg:.3f}"
        if sd['temps']:
            avg_t = safe_median(sd['temps'])
            line += f", avg temp {avg_t:.1f}°C"
        if sd['phs']:
            avg_p = safe_median(sd['phs'])
            line += f", avg pH {avg_p:.1f}"
        prods = list(sd['products'])[:2]
        if prods:
            line += f" ({', '.join(prods)})"
        lines.append(line)
    
    product_clause = (
        f" for {product_filter}" 
        if product_filter else ""
    )
    
    best_yield = ranked[0][0]
    most_studied = max(
        strain_data.items(),
        key=lambda x: x[1]['count']
    )[0]
    
    summary = (
        f"Strain analysis{product_clause} from "
        f"{len(filtered)} real records:\n\n" +
        '\n'.join(lines)
    )
    
    # Determine which unit dominated the ranking
    best_sd = strain_data.get(best_yield, {})
    used_unit = (
        'g/g' 
        if best_sd.get('gg_yields') 
        else 'g/L'
    )
    
    if best_yield == most_studied:
        summary += f"\n\nTop strain: {best_yield} "
        summary += (
            f"(highest yield AND most studied, "
            f"unit: {used_unit})"
        )
    else:
        summary += f"\n\nTop performer: {best_yield} "
        summary += (
            f"(by median yield, unit: {used_unit})"
        )
        summary += f"\nMost studied: {most_studied} "
        summary += f"(by paper count)"
    
    return summary


def answer_temperature(
    records: list, 
    all_data: list,
    product_filter: str = None,
    strain_filter: str = None
) -> str:
    """Return temperature statistics from real data."""
    
    source = all_data if all_data else records
    if product_filter:
        filtered_source = [
            r for r in source
            if product_filter.lower() in 
            (r.get('product') or '').lower()
        ]
        if filtered_source:
            source = filtered_source

    if strain_filter:
        strain_filtered = [
            r for r in source
            if strain_filter.lower() in 
            (normalize_strain(
                r.get('strain')
            ) or '').lower()
        ]
        if strain_filtered:
            source = strain_filtered
    temp_records = [
        r for r in source 
        if r.get('temperature') is not None
    ]
    
    if not temp_records:
        return None
    if len(temp_records) < 2:
        return (
            f"Only {len(temp_records)} temperature "
            f"record found — insufficient for reliable "
            f"statistics. Temperature is rarely "
            f"reported in abstracts."
        )
    
    temps = []
    for r in temp_records:
        try:
            temps.append(float(r['temperature']))
        except Exception:
            pass
    
    if not temps:
        return None
    
    avg = safe_median(temps)
    total = len(all_data) if all_data else len(records)
    coverage = len(temp_records) / total * 100 \
               if total else 0
    
    # Count by strain
    strain_temps = {}
    for r in temp_records:
        s = r.get('strain')
        t = r.get('temperature')
        if s and t:
            if s not in strain_temps:
                strain_temps[s] = []
            try:
                strain_temps[s].append(float(t))
            except Exception:
                pass
    
    result = (
        f"Temperature data from {len(temp_records)}"
        f"/{total} records "
        f"({coverage:.0f}% coverage):\n\n"
        f"Average: {avg:.1f}°C\n"
        f"Range: {min(temps):.1f}°C – "
        f"{max(temps):.1f}°C\n"
    )
    
    if strain_temps:
        result += "\nBy strain:\n"
        for s, t_list in sorted(
            strain_temps.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:4]:
            s_avg = safe_median(t_list) or 0
            result += (
                f"• {s}: {s_avg:.1f}°C "
                f"({len(t_list)} papers)\n"
            )
    
    result += (
        f"\n⚠ Temperature is missing from "
        f"{100-coverage:.0f}% of abstracts — "
        f"it lives in Materials & Methods sections."
    )
    
    return result


def answer_ph(
    records: list, 
    all_data: list,
    product_filter: str = None
) -> str:
    """Return pH statistics from real data."""
    
    source = all_data if all_data else records
    if product_filter:
        filtered_source = [
            r for r in source
            if product_filter.lower() in 
            (r.get('product') or '').lower()
        ]
        if filtered_source:
            source = filtered_source
    ph_records = [
        r for r in source 
        if r.get('ph') is not None
    ]
    
    if not ph_records:
        return None
    if len(ph_records) < 2:
        return (
            f"Only {len(ph_records)} pH record found "
            f"— insufficient for reliable statistics. "
            f"pH is rarely reported in abstracts."
        )
    
    phs = []
    for r in ph_records:
        try:
            phs.append(float(r['ph']))
        except Exception:
            pass
    
    if not phs:
        return None
    
    avg = safe_median(phs)
    total = len(all_data) if all_data else len(records)
    coverage = len(ph_records) / total * 100 \
               if total else 0
    
    return (
        f"pH data from {len(ph_records)}/{total} "
        f"records ({coverage:.0f}% coverage):\n\n"
        f"Average pH: {avg:.1f}\n"
        f"Range: {min(phs):.1f} – {max(phs):.1f}\n\n"
        f"⚠ pH is missing from "
        f"{100-coverage:.0f}% of abstracts."
    )


def answer_yield(
    records: list, 
    all_data: list,
    product_filter: str = None
) -> str:
    """Return yield statistics from real data."""
    
    source = all_data if all_data else records
    if product_filter:
        source = [
            r for r in source
            if product_filter.lower() in 
            (r.get('product') or '').lower()
        ]
    
    yield_records = [
        r for r in source 
        if r.get('yield_value') is not None
    ]
    
    if not yield_records:
        return None
    
    # Separate by unit — g/g and g/L cannot be 
    # compared directly
    gg_vals = []
    gl_vals = []
    other_vals = []
    
    for r in yield_records:
        try:
            v = float(r['yield_value'])
            unit = (r.get('yield_unit') or '').strip()
            if unit == 'g/g':
                gg_vals.append(v)
            elif unit == 'g/L':
                gl_vals.append(v)
            else:
                # Unknown unit — use value range 
                # to guess
                if v <= 1.5:
                    gg_vals.append(v)
                else:
                    gl_vals.append(v)
        except Exception:
            pass
    
    all_vals = gg_vals + gl_vals
    if not all_vals:
        return None
    
    total = len(source)
    coverage = len(yield_records) / total * 100 \
               if total else 0
    
    # Group by product
    prod_yields = {}
    for r in yield_records:
        p = r.get('product', 'unknown')
        y = r.get('yield_value')
        if y:
            if p not in prod_yields:
                prod_yields[p] = []
            try:
                prod_yields[p].append(float(y))
            except Exception:
                pass

    product_clause = (
        f" for {product_filter}" 
        if product_filter else ""
    )
    
    result = (
        f"Yield data{product_clause} from "
        f"{len(yield_records)}/{total} records:\n"
    )
    
    if gg_vals:
        med_gg = safe_median(gg_vals)
        result += (
            f"\ng/g (mass yield, {len(gg_vals)} records):\n"
            f"  Median: {med_gg:.3f} g/g\n"
            f"  Range: {min(gg_vals):.3f} – "
            f"{max(gg_vals):.3f} g/g\n"
        )
    
    if gl_vals:
        med_gl = safe_median(gl_vals)
        result += (
            f"\ng/L (titer, {len(gl_vals)} records):\n"
            f"  Median: {med_gl:.1f} g/L\n"
            f"  Range: {min(gl_vals):.1f} – "
            f"{max(gl_vals):.1f} g/L\n"
        )
    
    result += (
        f"\n⚠ g/g and g/L cannot be directly "
        f"compared — they measure different things "
        f"(mass ratio vs concentration).\n"
    )

    if prod_yields and not product_filter:
        result += "\nBy product:\n"
        for p, y_list in sorted(
            prod_yields.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:5]:
            p_avg = safe_median(y_list) or 0
            result += (
                f"• {p}: avg {p_avg:.3f} "
                f"({len(y_list)} records)\n"
            )
            
        result += (
            "\n⚠ Product averages mix g/g and g/L "
            "values — interpret with caution.\n"
        )
    
    return result


def answer_compare(
    records: list, 
    all_data: list,
    strain_a: str = None,
    strain_b: str = None
) -> str:
    """Compare two strains from real data."""
    
    source = all_data if all_data else records
    
    def get_strain_stats(strain_name):
        recs = [
            r for r in source
            if strain_name.lower() in 
            (normalize_strain(r.get('strain')) or '').lower()
        ]
        if not recs:
            return None
        yields = [
            float(r['yield_value']) 
            for r in recs 
            if r.get('yield_value')
        ]
        temps = [
            float(r['temperature']) 
            for r in recs 
            if r.get('temperature')
        ]
        phs = [
            float(r['ph']) 
            for r in recs 
            if r.get('ph')
        ]
        products = list(set(
            r.get('product') 
            for r in recs 
            if r.get('product')
        ))
        return {
            'count': len(recs),
            'avg_yield': safe_median(yields),
            'avg_temp': safe_median(temps),
            'avg_ph': safe_median(phs),
            'products': products[:3],
        }
    
    # Auto-detect strains from records if not specified
    if not strain_a or not strain_b:
        all_strains = list(set(
            r.get('strain') 
            for r in source 
            if r.get('strain')
        ))
        if len(all_strains) >= 2:
            strain_a = strain_a or all_strains[0]
            strain_b = strain_b or all_strains[1]
        else:
            return None
    
    stats_a = get_strain_stats(strain_a)
    stats_b = get_strain_stats(strain_b)
    
    if not stats_a and not stats_b:
        return None
    
    def format_stats(name, stats):
        if not stats:
            return f"{name}: No data found"
        lines = [
            f"📊 {name} ({stats['count']} papers):"
        ]
        if stats['avg_yield'] is not None:
            lines.append(
                f"  Yield: {stats['avg_yield']:.3f}"
            )
        if stats['avg_temp'] is not None:
            lines.append(
                f"  Temp: {stats['avg_temp']:.1f}°C"
            )
        if stats['avg_ph'] is not None:
            lines.append(
                f"  pH: {stats['avg_ph']:.1f}"
            )
        if stats['products']:
            lines.append(
                f"  Products: "
                f"{', '.join(stats['products'])}"
            )
        return '\n'.join(lines)
    
    return (
        f"Strain comparison from real literature:\n\n"
        f"{format_stats(strain_a, stats_a)}\n\n"
        f"{format_stats(strain_b, stats_b)}"
    )


def answer_data_gap(all_data: list) -> str:
    """Report data availability gaps from real data."""
    if not all_data:
        return None
    
    n = len(all_data)
    
    def pct(count):
        return f"{count}/{n} = {count/n*100:.0f}%"
    
    strain_c = sum(
        1 for r in all_data if r.get('strain')
    )
    temp_c = sum(
        1 for r in all_data if r.get('temperature')
    )
    ph_c = sum(
        1 for r in all_data if r.get('ph')
    )
    yield_c = sum(
        1 for r in all_data if r.get('yield_value')
    )
    medium_c = sum(
        1 for r in all_data if r.get('medium')
    )
    ft_c = sum(
        1 for r in all_data
        if r.get('data_source') in (
            'fulltext', 'pmc_fulltext'
        )
    )
    
    return (
        f"Data availability from {n} real records:\n\n"
        f"• Strain name:   {pct(strain_c)}\n"
        f"• Yield value:   {pct(yield_c)}\n"
        f"• Temperature:   {pct(temp_c)}\n"
        f"• pH:            {pct(ph_c)}\n"
        f"• Medium:        {pct(medium_c)}\n"
        f"• Full text:     {pct(ft_c)}\n\n"
        f"Core finding: Temperature and pH are "
        f"systematically absent from abstracts "
        f"but present in Materials & Methods "
        f"sections. Full-text mining via PMC and "
        f"Unpaywall is essential for complete data."
    )


def build_context(records: list) -> str:
    """Build structured context from records.
    No truncation. No summarization.
    Each record clearly formatted."""
    if not records:
        return "No relevant records found."
    
    def is_valid_record(r):
        """Filter out obvious extraction artifacts."""
        y = r.get('yield_value')
        if y is not None:
            try:
                float(y)
            except (TypeError, ValueError):
                return False
        return True

    lines = []
    for i, r in enumerate(
        [r for r in records if is_valid_record(r)], 1
    ):
        parts = []
        if r.get('strain'):
            parts.append(f"Strain: {r['strain']}")
        if r.get('product'):
            parts.append(f"Product: {r['product']}")
        if r.get('yield_value'):
            try:
                yv = float(r['yield_value'])
                unit = r.get('yield_unit') or 'g/g'
                # Sanity check — reject physically 
                # impossible values
                if unit == 'g/g' and 0 < yv <= 1.5:
                    parts.append(
                        f"Yield: {yv:.3f} {unit}"
                    )
                elif unit == 'g/L' and 0 < yv <= 500:
                    parts.append(
                        f"Yield: {yv:.1f} {unit}"
                    )
                elif unit not in ('g/g', 'g/L'):
                    # Unknown unit — only show if 
                    # value is in plausible range
                    if 0 < yv <= 500:
                        parts.append(
                            f"Yield: {yv:.3f} {unit}"
                        )
            except Exception:
                pass  # Skip malformed yield values
        if r.get('temperature') is not None:
            parts.append(
                f"Temp: {r['temperature']}°C"
            )
        if r.get('ph') is not None:
            parts.append(f"pH: {r['ph']}")
        if r.get('medium'):
            parts.append(f"Medium: {r['medium']}")
        if r.get('carbon_source'):
            parts.append(
                f"Carbon: {r['carbon_source']}"
            )
        pmid = r.get('PMID', '')
        if pmid:
            parts.append(f"PMID: {pmid}")
        
        src = r.get('data_source', 'abstract')
        src_label = (
            '[Full Text]' 
            if src in ('fulltext', 'pmc_fulltext')
            else '[Abstract]'
        )
        
        lines.append(
            f"{i}. {', '.join(parts)} {src_label}"
        )
    
    return '\n'.join(lines)


def build_gpt_prompt(
    question: str, 
    records: list,
    question_type: str
) -> str:
    """Build a structured prompt for GPT-2 
    from real extracted records."""
    
    if not records:
        # No real data — use knowledge prompt
        if question_type == 'strain':
            return (
                f"E. coli strain recommendation "
                f"for {question}: "
                f"Based on fermentation literature,"
            )
        else:
            return (
                f"E. coli fermentation literature "
                f"analysis for {question}: "
            )
    
    # Build context from real records
    context_lines = []
    for r in records:
        strain = r.get('strain') or 'Unknown strain'
        product = r.get('product') or 'product'
        
        parts = [f"E. coli {strain}"]
        parts.append(f"for {product}")
        
        if r.get('yield_value'):
            unit = r.get('yield_unit') or 'g/g'
            parts.append(
                f"yield {r['yield_value']:.3f} {unit}"
            )
        if r.get('temperature'):
            parts.append(
                f"at {r['temperature']}°C"
            )
        if r.get('ph'):
            parts.append(f"pH {r['ph']}")
        if r.get('medium') and r['medium'] != 'Custom':
            parts.append(f"in {r['medium']} medium")
        
        context_lines.append('. '.join(parts) + '.')
    
    context = ' '.join(context_lines)
    
    # Build final prompt based on question type
    if question_type == 'best_strain':
        prompt = (
            f"Literature data on E. coli "
            f"fermentation: {context} "
            f"Conclusion on best strain:"
        )
    elif question_type == 'temperature':
        prompt = (
            f"E. coli cultivation temperature "
            f"data from literature: {context} "
            f"Temperature summary:"
        )
    elif question_type == 'yield':
        prompt = (
            f"E. coli yield data from "
            f"published experiments: {context} "
            f"Yield analysis:"
        )
    elif question_type == 'ph':
        prompt = (
            f"E. coli fermentation pH data: "
            f"{context} "
            f"pH recommendation:"
        )
    elif question_type == 'compare':
        prompt = (
            f"Comparison of E. coli strains "
            f"from literature: {context} "
            f"Comparison result:"
        )
    else:
        prompt = (
            f"E. coli fermentation literature "
            f"summary: {context} "
            f"Key finding:"
        )
    
    # Limit prompt length to 200 chars 
    # for GPT-2 small
    if len(prompt) > 250:
        prompt = prompt[:250]
    
    return prompt


def classify_question(question: str) -> str:
    """Classify question into a type for 
    prompt building."""
    q = question.lower()
    
    if any(w in q for w in [
        'best strain', 'best for', 
        'which strain', 'recommend'
    ]):
        return 'best_strain'
    elif any(w in q for w in [
        'temperature', 'temp', 
        'degrees', 'celsius', '°c'
    ]):
        return 'temperature'
    elif any(w in q for w in [
        'yield', 'how much', 
        'productivity', 'titer'
    ]):
        return 'yield'
    elif any(w in q for w in [
        'ph', 'acidity', 'acidic'
    ]):
        return 'ph'
    elif any(w in q for w in [
        'compare', 'vs', 'versus', 
        'difference', 'better'
    ]):
        return 'compare'
    elif any(w in q for w in [
        'gap', 'missing', 'available',
        'abstract', 'fulltext'
    ]):
        return 'data_gap'
    else:
        return 'general'


def clean_gpt_output(text: str) -> str:
    """Clean GPT-2 output — remove repetitions,
    truncate at natural sentence end,
    ensure it reads like a real answer."""
    if not text:
        return ""
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Truncate at last complete sentence
    for punct in ['. ', '.\n', '! ', '? ']:
        last = text.rfind(punct)
        if last > 30:  # At least 30 chars
            text = text[:last + 1]
            break
    
    # Remove if too short to be useful
    if len(text) < 20:
        return ""
    
    # Remove obvious repetitions
    sentences = text.split('. ')
    seen = set()
    unique = []
    for s in sentences:
        s_clean = s.strip().lower()
        if s_clean and s_clean not in seen:
            seen.add(s_clean)
            unique.append(s.strip())
    
    result = '. '.join(unique)
    if result and not result.endswith('.'):
        result += '.'
    
    return result

# API endpoints
@app.get("/", response_class=HTMLResponse)
async def home():
    """Main homepage"""
    return HTMLResponse(content=HTML_PAGE)

@app.get("/health")
async def health_check():
    """Health endpoint"""
    return {
        "status": "healthy",
        "service": "E. coli GPT Enhanced",
        "server": "93.127.214.36",
        "location": "/var/www/html/ecoli-gpt/",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "features": ["paper_input", "progress_bar", "results_table", "metrics"],
        "gpt2_model": {
            "available": gpt_model.is_available,
            "path": EColiGPTModel.MODEL_PATH,
            "status": (
                "ready" if gpt_model.is_available 
                else "not_trained"
            ),
        },
    }

analysis_status = {}

@app.get("/api/analyze/status/{job_id}")
async def get_analysis_status(job_id: str):
    """Get real-time status of an analysis job."""
    status = analysis_status.get(job_id, {
        "step": 0,
        "total_steps": 5,
        "message": "Starting...",
        "done": False,
        "error": None,
    })
    return status

@app.get("/strains")
async def get_strains():
    """Get all strain data"""
    strains = [
        {"name": "BL21(DE3)", "description": "Protein production workhorse", "optimal_temp": 37},
        {"name": "K-12", "description": "Laboratory standard strain", "optimal_temp": 37},
        {"name": "MG1655", "description": "Wild-type reference strain", "optimal_temp": 37},
        {"name": "W3110", "description": "Derivative of K-12", "optimal_temp": 37},
        {"name": "FOR", "description": "Ethanol-tolerant strain", "optimal_temp": 32},
    ]
    return strains

def _flatten_for_csv(structured: list) -> list:
    """Flatten structured data for CSV export (tabular format). Missing values as empty."""
    rows = []
    for item in structured:
        strain = item.get("strain") or {}
        strain_name = strain.get("name") if isinstance(strain, dict) else (strain if strain else None)
        if strain_name == "Unknown" or strain_name == "":
            strain_name = None
        temp = item.get("temperature") or {}
        temp_val = temp.get("value") if isinstance(temp, dict) else None
        ph = item.get("ph") or {}
        ph_val = ph.get("value") if isinstance(ph, dict) else None
        medium = item.get("medium")
        if medium in (None, "", "Custom"):
            medium = None
        carbon_source = item.get("carbon_source")
        if carbon_source in (None, "", "unknown"):
            carbon_source = None
        ds = item.get("data_source") or item.get("literature_source") or ""
        data_source = "fulltext" if ds == "pmc_fulltext" else "abstract"

        raw_unit = item.get("yield_unit", "")
        if raw_unit in ("dimensionless", "", None):
            yv = item.get("yield_value")
            if yv is not None:
                try:
                    yv_f = float(yv)
                    if 0.001 <= yv_f <= 1.5:
                        clean_unit = "g/g"
                    elif yv_f > 1.5:
                        clean_unit = "g/L"
                    else:
                        clean_unit = None
                except Exception:
                    clean_unit = None
            else:
                clean_unit = None
        elif raw_unit in ("g/g", "g/L", "%"):
            clean_unit = raw_unit
        else:
            clean_unit = None

        rows.append({
            "PMID": item.get("paper_id"),
            "data_source": data_source,
            "strain": strain_name,
            "strain_genotype": item.get("strain_genotype") or None,
            "strain_source": item.get("strain_source") or None,
            "product": item.get("product") or None,
            "yield_value": item.get("yield_value"),
            "yield_unit": clean_unit,
            "temperature": temp_val,
            "ph": ph_val,
            "medium": medium,
            "carbon_source": carbon_source,
            "confidence": item.get("confidence"),
        })
    return rows


def _transform_to_api_format(structured: list) -> list:
    """Transform pipeline output to API results. Missing values are null, no placeholders."""
    results = []
    for item in structured:
        strain = item.get('strain')
        strain_name = strain.get('name') if isinstance(strain, dict) else (strain if strain else None)
        if strain_name == 'Unknown' or strain_name == '':
            strain_name = None

        temp_data = item.get('temperature')
        temp_val = temp_data.get('value') if isinstance(temp_data, dict) and temp_data else None
        if temp_val is not None:
            temp_val = round(temp_val, 1) if isinstance(temp_val, float) else temp_val

        ph_data = item.get('ph')
        ph_val = ph_data.get('value') if isinstance(ph_data, dict) and ph_data else None
        if ph_val is not None:
            ph_val = round(ph_val, 1) if isinstance(ph_val, float) else ph_val

        product = item.get('product') or None
        if product == '':
            product = None

        medium = item.get('medium')
        if medium in (None, '', 'Custom'):
            medium = None

        carbon_source = item.get('carbon_source')
        if carbon_source in (None, '', 'unknown'):
            carbon_source = None

        yield_value = item.get('yield_value')
        raw_unit = item.get('yield_unit', '')
        
        # Clean up unit
        if raw_unit in ('', 'dimensionless', None):
            # If yield value looks like g/g range (0.01-1.5)
            # assign g/g, otherwise leave blank
            if yield_value is not None:
                if 0.001 <= float(yield_value) <= 1.5:
                    yield_unit = 'g/g'
                elif float(yield_value) > 1.5:
                    yield_unit = 'g/L'
                else:
                    yield_unit = None
            else:
                yield_unit = None
        elif raw_unit in ('g/g', 'g/L', '%'):
            yield_unit = raw_unit
        else:
            yield_unit = None

        conf = item.get('confidence')
        confidence = round(float(conf), 2) if conf is not None else None

        record = {
            'PMID': item.get('paper_id'),
            'strain': strain_name,
            'product': product,
            'yield_value': yield_value,
            'yield_unit': yield_unit,
            'temperature': temp_val,
            'ph': ph_val,
            'medium': medium,
            'carbon_source': carbon_source,
            'confidence': confidence,
            'data_source': (
                item.get('data_source') or 
                item.get('literature_source') or 
                'abstract'
            ),
        }
        record['yield'] = yield_value  # alias for frontend table
        results.append(record)
    return results


@app.get("/api/analyze")
async def analyze_papers(
    year_from: int = 2020,
    year_to: Optional[int] = None,
    to_present: bool = False,
    max_results: int = 500,
):
    """Analyze PubMed papers by publication year 
    range using ScientificPubMedEColiExtractor."""
    current_year = datetime.now().year
    yf = max(1950, min(year_from, current_year))
    if to_present or year_to is None:
        yt = current_year
        range_label = f"{yf}–present"
    else:
        yt = max(1950, min(year_to, current_year))
        if yt < yf:
            yf, yt = yt, yf
        range_label = f"{yf}–{yt}"
    max_results = max(1, min(max_results, 1000))

    try:
        extractor = ScientificPubMedEColiExtractor()

        pmids, _pmc_map = await asyncio.to_thread(
            extractor.search_data_rich_papers,
            max_results, yf, yt,
        )

        if not pmids:
            return {
                "status": "success",
                "analysis_id": datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                ),
                "records_found": 0,
                "results": [],
                "year_from": yf,
                "year_to": yt,
                "publication_range_label": range_label,
                "statistics": {
                    "temperature_coverage": "0%",
                    "ph_coverage": "0%",
                    "average_yield": 0,
                    "temp_coverage_pct": "0%",
                    "ph_coverage_pct": "0%",
                    "average_confidence_pct": "0%",
                    "strain_coverage": "0%",
                    "strain_coverage_pct": "0%",
                    "key_finding": (
                        f"No papers found for "
                        f"{range_label}."
                    ),
                },
                "comparison": None,
                "year_distribution": {},
                "timestamp": datetime.now().isoformat(),
            }

        # Step 1: fetch abstracts
        papers_abstract = await asyncio.to_thread(
            extractor.fetch_paper_data, pmids, False
        )

        # Step 2a: PMC elink
        elink_pmc_list = []
        elink_pmid_by_pmc: Dict[str, str] = {}
        if _pmc_map:
            for pmid_k, pmcid_v in _pmc_map.items():
                pk = str(pmcid_v).strip()
                if not pk.upper().startswith("PMC"):
                    pk = "PMC" + pk.lstrip("0")
                elink_pmc_list.append(pk)
                elink_pmid_by_pmc[pk.upper()] = str(
                    pmid_k
                )

        # Step 2b: PMC direct search
        pmc_direct_ids: list = []
        try:
            pmc_direct_ids = await asyncio.to_thread(
                extractor.search_pmc_directly,
                200, yf, yt,
            )
        except Exception:
            pmc_direct_ids = []

        pmc_direct_pmid_map = {}
        if pmc_direct_ids:
            try:
                pmc_direct_pmid_map = (
                    await asyncio.to_thread(
                        extractor._elink_pmc_to_pubmed,
                        pmc_direct_ids,
                    )
                )
            except Exception:
                pass

        combined_pmc: Dict[str, str] = {}
        for pk, pmid in elink_pmid_by_pmc.items():
            combined_pmc[pk.upper()] = pmid
        for pmcid, pmid in pmc_direct_pmid_map.items():
            pk = str(pmcid).strip()
            if not pk.upper().startswith("PMC"):
                pk = "PMC" + pk.lstrip("0")
            if pk.upper() not in combined_pmc:
                combined_pmc[pk.upper()] = str(pmid)

        combined_pmc_list = list(combined_pmc.keys())
        pmid_by_combined_pmc = dict(combined_pmc.items())

        pmc_papers = []
        if combined_pmc_list:
            try:
                pmc_papers = await asyncio.to_thread(
                    extractor.fetch_fulltext_pmc,
                    combined_pmc_list,
                    pmid_by_combined_pmc,
                )
            except Exception:
                pmc_papers = []

        # Step 2c: Unpaywall
        pmids_with_ft = set(
            str(p.get("pmid", ""))
            for p in pmc_papers
            if p.get("pmid")
        )
        pmids_for_unpaywall = [
            p for p in pmids
            if str(p) not in pmids_with_ft
        ]
        unpaywall_papers: list = []
        if pmids_for_unpaywall:
            try:
                unpaywall_papers = (
                    await asyncio.to_thread(
                        extractor.fetch_fulltext_unpaywall,
                        pmids_for_unpaywall,
                    )
                )
            except Exception:
                unpaywall_papers = []

        all_fulltext = pmc_papers + unpaywall_papers

        # Step 3: merge
        if all_fulltext:
            merged_papers = await asyncio.to_thread(
                extractor.merge_abstract_and_fulltext,
                papers_abstract,
                all_fulltext,
            )
        else:
            merged_papers = papers_abstract

        # Step 4: extract
        structured_data = await asyncio.to_thread(
            extractor.extract_structured_data,
            merged_papers,
        )

        n = len(structured_data)

        # Statistics
        temp_count = sum(
            1 for r in structured_data
            if r.get("temperature")
        )
        ph_count = sum(
            1 for r in structured_data
            if r.get("ph")
        )
        yield_values = [
            r["yield_value"]
            for r in structured_data
            if r.get("yield_value")
        ]
        confidence_values = [
            r.get("confidence", 0)
            for r in structured_data
        ]
        strain_count = sum(
            1 for r in structured_data
            if r.get("strain") and (
                r["strain"].get("name")
                if isinstance(r["strain"], dict)
                else r["strain"]
            ) not in (None, "", "Unknown")
        )

        temperature_coverage_pct = (
            temp_count / n * 100
        ) if n else 0
        ph_coverage_pct = (
            ph_count / n * 100
        ) if n else 0
        strain_coverage_pct = (
            strain_count / n * 100
        ) if n else 0
        average_yield = round(
            sum(yield_values) / len(yield_values), 3
        ) if yield_values else 0
        average_confidence = round(
            sum(confidence_values) /
            len(confidence_values) * 100
        ) if confidence_values else 0

        # Comparison
        abs_records = [
            r for r in structured_data
            if r.get("data_source") != "pmc_fulltext"
        ]
        ft_records = [
            r for r in structured_data
            if r.get("data_source") == "pmc_fulltext"
        ]

        def _has_val(rec, key):
            v = rec.get(key)
            if not v:
                return False
            if isinstance(v, dict):
                return bool(v.get("value"))
            return True

        def _pct_str(count, total):
            if total == 0:
                return "0%"
            return f"{count / total * 100:.1f}%"

        def _strain_filled(recs):
            return sum(
                1 for r in recs
                if r.get("strain") and (
                    r["strain"].get("name")
                    if isinstance(r["strain"], dict)
                    else r["strain"]
                ) not in (None, "", "Unknown")
            )

        pmc_summary = getattr(
            extractor,
            "_pmc_fetch_summary",
            {"success": 0, "failed": 0, "fallback": 0},
        )

        comparison = {
            "abstract_records": len(abs_records),
            "fulltext_records": len(ft_records),
            "abstract": {
                "strain_name": _pct_str(
                    _strain_filled(abs_records),
                    len(abs_records)
                ),
                "temperature": _pct_str(
                    sum(1 for r in abs_records
                        if _has_val(r, "temperature")),
                    len(abs_records)
                ),
                "ph": _pct_str(
                    sum(1 for r in abs_records
                        if _has_val(r, "ph")),
                    len(abs_records)
                ),
                "yield": _pct_str(
                    sum(1 for r in abs_records
                        if r.get("yield_value")),
                    len(abs_records)
                ),
            },
            "fulltext": {
                "strain_name": _pct_str(
                    _strain_filled(ft_records),
                    len(ft_records)
                ),
                "temperature": _pct_str(
                    sum(1 for r in ft_records
                        if _has_val(r, "temperature")),
                    len(ft_records)
                ),
                "ph": _pct_str(
                    sum(1 for r in ft_records
                        if _has_val(r, "ph")),
                    len(ft_records)
                ),
                "yield": _pct_str(
                    sum(1 for r in ft_records
                        if r.get("yield_value")),
                    len(ft_records)
                ),
            },
            "pmc_fetch": pmc_summary,
        }

        # Year distribution
        year_distribution = {}
        for r in structured_data:
            yr = str(r.get("year", ""))[:4]
            if yr.isdigit() and 1990 <= int(yr) <= 2030:
                year_distribution[yr] = (
                    year_distribution.get(yr, 0) + 1
                )
        year_distribution = dict(
            sorted(year_distribution.items())
        )

        # Sort results by completeness
        results_for_frontend = _transform_to_api_format(
            structured_data
        )

        def count_filled(rec):
            return sum(1 for f in [
                rec.get("strain"),
                rec.get("temperature"),
                rec.get("ph"),
                rec.get("yield_value"),
                rec.get("medium"),
            ] if f is not None and f != "")

        results_sorted = sorted(
            results_for_frontend,
            key=count_filled,
            reverse=True,
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
        analysis_id = timestamp
        analyses[analysis_id] = {
            "id": analysis_id,
            "results": results_for_frontend,
            "timestamp": datetime.now().isoformat(),
        }

        with open(
            f"ecoli_dataset_{timestamp}.json",
            "w", encoding="utf-8"
        ) as f:
            json.dump(structured_data, f, indent=2)

        if structured_data:
            flat_for_csv = _flatten_for_csv(
                structured_data
            )
            if flat_for_csv:
                with open(
                    f"ecoli_dataset_{timestamp}.csv",
                    "w", newline="", encoding="utf-8"
                ) as f:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=flat_for_csv[0].keys()
                    )
                    writer.writeheader()
                    writer.writerows(flat_for_csv)

        return {
            "status": "success",
            "analysis_id": analysis_id,
            "records_found": n,
            "results": results_sorted[:10],
            "year_from": yf,
            "year_to": yt,
            "publication_range_label": range_label,
            "statistics": {
                "temperature_coverage": (
                    f"{temperature_coverage_pct:.1f}%"
                ),
                "ph_coverage": (
                    f"{ph_coverage_pct:.1f}%"
                ),
                "average_yield": average_yield,
                "average_confidence": average_confidence,
                "avg_confidence": (
                    f"{average_confidence}%"
                ),
                "temp_coverage_pct": (
                    f"{temperature_coverage_pct:.0f}%"
                ),
                "ph_coverage_pct": (
                    f"{ph_coverage_pct:.0f}%"
                ),
                "average_confidence_pct": (
                    f"{average_confidence}%"
                ),
                "strain_coverage": (
                    f"{strain_coverage_pct:.1f}%"
                ),
                "strain_coverage_pct": (
                    f"{strain_coverage_pct:.0f}%"
                ),
                "key_finding": (
                    f"Range {range_label}: "
                    f"extracted {n} records. "
                    f"Fulltext: PMC "
                    f"{len(pmc_papers)}, "
                    f"Unpaywall "
                    f"{len(unpaywall_papers)}. "
                    + (
                        f"Only "
                        f"{temperature_coverage_pct:.0f}"
                        f"% report temperature!"
                        if n else ""
                    )
                ),
            },
            "comparison": comparison,
            "year_distribution": year_distribution,
            "pmc_direct_found": len(pmc_direct_ids),
            "pmc_fulltext_fetched": len(pmc_papers),
            "unpaywall_fetched": len(unpaywall_papers),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=str(e)
        )


@app.post("/api/query")
async def query_system(request: QueryRequest):
    """Scientific Q&A grounded in real extracted data.
    Rule-based answering is primary.
    GPT-2 used only for explanation when 
    rule-based has insufficient data."""
    try:
        question = request.question
        
        import re as _re2

        # Reject queries with no alphabetic content
        if not _re2.search(r"[a-zA-Z]", question):
            return {
                "question": question,
                "answer": (
                    "Query not recognized. Please ask about "
                    "E. coli strains, yield, temperature, pH, "
                    "or fermentation products."
                ),
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.0,
                "method": "invalid_query",
                "records_used": 0,
                "total_records": 0,
                "gpt2_available": gpt_model.is_available,
            }
        
        # Detect gibberish — no known scientific keywords
        _valid_keywords = [
            'strain', 'yield', 'temperature', 'temp',
            'ph', 'compare', 'best', 'production', 
            'ethanol', 'protein', 'acid', 'data', 
            'missing', 'coverage', 'full', 'analysis',
            'ferment', 'medium', 'carbon', 'culture',
            'bioreactor', 'batch', 'performance',
            'which', 'what', 'how', 'give', 'show',
            'enzyme', 'pha', 'lactic', 'succinic',
            'acetic', 'butanol', 'statistics', 'stats',
            'average', 'range', 'highest', 'lowest',
            'complete', 'dataset', 'available',
        ]
        
        q_lower_check = question.lower()
        
        if not any(k in q_lower_check for k in _valid_keywords):
            return {
                "question": question,
                "answer": (
                    "Query not recognized. "
                    "Try asking about:\n"
                    "• Best strain for a product\n"
                    "• Yield or temperature statistics\n"
                    "• Strain comparison (e.g. BL21 vs MG1655)\n"
                    "• Data availability gaps\n"
                    "• Full analysis of a product"
                ),
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.2,
                "method": "invalid_query",
                "records_used": 0,
                "total_records": 0,
                "gpt2_available": gpt_model.is_available,
            }

        q_lower = question.lower()

        # Get full dataset
        all_data = get_all_real_data()

        # Retrieve relevant records
        relevant = retrieve_relevant_records(
            q_lower, max_records=5
        )

        # Classify question
        q_type = classify_question(q_lower)

        # Detect product and strain filters
        import re as _re

        product_filter = None
        _products = [
            'succinic acid', 'lactic acid', 'acetic acid',
            'ethanol', 'protein', 'butanol', 'enzyme', 'pha',
        ]
        for _p in _products:
            if _re.search(
                rf"\b{_re.escape(_p)}\b", 
                q_lower
            ):
                product_filter = _p
                break

        strain_a = None
        strain_b = None
        strain_list = [
            'bl21', 'mg1655', 'k-12', 'w3110',
            'dh5', 'jm109', 'bw25113', 'for',
            'rosetta', 'xl1', 'top10', 'dh10b',
        ]
        found_strains = [
            s for s in strain_list 
            if s in q_lower
        ]
        if len(found_strains) >= 2:
            strain_a = found_strains[0]
            strain_b = found_strains[1]
        elif len(found_strains) == 1:
            strain_a = found_strains[0]

        # Try rule-based answering first
        rule_answer = None
        method = "rule_based"

        # Full analysis — combines all answer types
        if any(phrase in q_lower for phrase in [
            'full analysis', 'complete analysis',
            'analyze', 'tell me everything',
            'full report', 'overview',
        ]):
            p_filter = product_filter
            
            parts = []
            
            best = answer_best_strain(
                relevant, all_data, p_filter
            )
            if best:
                parts.append("## Best Strain\n" + best)
            
            yld = answer_yield(
                relevant, all_data, p_filter
            )
            if yld:
                parts.append("## Yield Statistics\n" + yld)
            
            temp = answer_temperature(
                relevant, all_data, p_filter
            )
            if temp:
                parts.append(
                    "## Temperature Data\n" + temp
                )
            
            ph = answer_ph(
                relevant, all_data, p_filter
            )
            if ph:
                parts.append("## pH Data\n" + ph)
            
            gaps = answer_data_gap(all_data)
            if gaps and not p_filter:
                parts.append(
                    "## Data Availability\n" + gaps
                )
            
            if parts:
                rule_answer = "\n\n".join(parts)
                method = "full_analysis"

        elif q_type == 'best_strain':
            rule_answer = answer_best_strain(
                relevant, all_data, product_filter
            )

        elif q_type == 'temperature':
            rule_answer = answer_temperature(
                relevant, all_data, 
                product_filter,
                strain_a  # pass detected strain as filter
            )

        elif q_type == 'ph':
            rule_answer = answer_ph(
                relevant, all_data, product_filter
            )

        elif q_type == 'yield':
            rule_answer = answer_yield(
                relevant, all_data, product_filter
            )

        elif q_type == 'compare':
            rule_answer = answer_compare(
                relevant, all_data, 
                strain_a, strain_b
            )

        elif q_type == 'data_gap':
            rule_answer = answer_data_gap(all_data)

        # If rule-based gave a good answer, use it
        if rule_answer and len(rule_answer) > 30:
            answer = rule_answer
            
            # Optionally append GPT-2 one-line 
            # supplement if model available
            if (
                gpt_model.is_available 
                and len(relevant) >= 2
            ):
                # GPT-2 disabled — output is repetitive and adds
                # no value over the rule-based answers
                pass
        
        else:
            # Rule-based failed — use GPT-2 with context
            method = "gpt2_with_context"
            
            if gpt_model.is_available and relevant:
                # GPT-2 disabled
                pass
                method = "fallback"
                answer = _fallback_answer(
                    q_lower, all_data,
                    q_type, product_filter
                )
            else:
                method = "fallback"
                answer = _fallback_answer(
                    q_lower, all_data,
                    q_type, product_filter
                )

        # Handle follow-up context from history
        last_strain = None
        for h in reversed(request.history or []):
            prev = (
                h.get('answer','') + ' ' + 
                h.get('question','')
            ).lower()
            for s in strain_list:
                if s in prev:
                    last_strain = s.upper()
                    break
            if last_strain:
                break

        if (
            last_strain
            and len(q_lower.split()) <= 4
            and q_type == "general"
            and not any(kw in q_lower for kw in [
                'complete', 'dataset', 'missing',
                'available', 'coverage', 'analysis',
                'full', 'all', 'how many', 'statistics',
            ])
        ):
            follow_recs = [
                r for r in all_data
                if last_strain.lower() in 
                (r.get('strain') or '').lower()
            ]
            if follow_recs:
                answer = (
                    f"For {last_strain} "
                    f"({len(follow_recs)} records):\n"
                ) + build_context(
                    follow_recs[:4]
                )

        _data_size = len(all_data)
        _base_conf = (
            0.9 if _data_size > 100
            else 0.8 if _data_size > 50
            else 0.7 if _data_size > 10
            else 0.5
        )
        _method_mult = (
            1.0 if method == "rule_based"
            else 0.95 if method == "full_analysis"
            else 0.85 if "gpt2" in method
            else 0.7
        )

        return {
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat(),
            "confidence": round(_base_conf * _method_mult, 2),
            "method": method,
            "records_used": len(relevant),
            "total_records": len(all_data),
            "gpt2_available": gpt_model.is_available,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=str(e)
        )


def _fallback_answer(
    q_lower: str, 
    all_data: list,
    q_type: str,
    product_filter: str
) -> str:
    """Last resort fallback when rule-based and 
    GPT-2 both fail or unavailable."""
    if not all_data:
        return (
            "Run an analysis first to see data.\n"
            "Use the Analyze PubMed Papers section above."
        )
    n = len(all_data)
    ft = sum(
        1 for r in all_data
        if r.get('data_source') in (
            'fulltext','pmc_fulltext'
        )
    )
    return (
        f"Your analysis contains {n} records "
        f"({ft} from full text).\n\n"
        f"Ask about:\n"
        f"• Best strain for a product\n"
        f"• Yield statistics\n"
        f"• Temperature or pH coverage\n"
        f"• Strain comparison (e.g. BL21 vs MG1655)\n"
        f"• Data gaps\n\n"
        f"Train GPT-2 via pipeline.py for "
        f"richer analysis."
    )


@app.get("/stats")
async def get_stats():
    """Get server statistics"""
    total_records = sum(len(a["results"]) for a in analyses.values())
    
    return {
        "server": "93.127.214.36",
        "status": "running",
        "version": "2.0.0 (Enhanced)",
        "uptime": "Active",
        "total_analyses": len(analyses),
        "total_records": total_records,
        "current_time": datetime.now().isoformat(),
        "features": [
            "Interactive paper analysis with slider",
            "Progress bar for analysis",
            "Results table with sorting",
            "Metrics dashboard",
            "Question-answer interface",
            "Data gaps analysis"
        ]
    }

@app.get("/api/download/csv")
async def download_latest_csv():
    """Download the most recently generated 
    CSV dataset file."""
    import os
    import glob
    from fastapi.responses import FileResponse
    
    # Find the most recent CSV file
    csv_files = glob.glob("ecoli_dataset_*.csv")
    
    if not csv_files:
        raise HTTPException(
            status_code=404,
            detail="No CSV file found. "
                   "Run an analysis first."
        )
    
    # Sort by modification time, get most recent
    latest_csv = max(
        csv_files, 
        key=os.path.getmtime
    )
    
    return FileResponse(
        path=latest_csv,
        media_type="text/csv",
        filename=f"ecoli_gpt_data_{latest_csv}",
    )

# Main execution
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("E. COLI GPT ENHANCED SERVER")
    print("=" * 70)
    print("Features Added:")
    print("  - Number of Papers slider (10-500)")
    print("  - Progress bar during analysis")
    print("  - Results table with proper formatting")
    print("  - Metrics dashboard")
    print("  - Enhanced question-answer interface")
    print("  - Data gaps analysis")
    print("=" * 70)
    print("Server will be available at: http://93.127.214.36:8000")
    print("Press Ctrl+C to stop")
    print("=" * 70)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )