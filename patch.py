import sys
import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# CHANGE 1
content = content.replace("analyses = {}\n", "analyses = {}\nimport asyncio as _asyncio\ntask_results: dict = {}\n")

# CHANGE 5 — Update frontend analyzePapers function (replace the whole function between 'async function analyzePapers() {' and 'function showAnalysisResults(data) {')
frontend_pattern = re.compile(
    r'(async function analyzePapers\(\) \{.*?\n        \})\n        \n        function showAnalysisResults',
    re.DOTALL
)

frontend_replacement = """async function analyzePapers() {
            const cy = new Date().getFullYear();
            let yf = parseInt(
                document.getElementById('yearFrom').value,10
            );
            if (isNaN(yf)) yf = 2020;
            yf = Math.max(1950, Math.min(yf, cy));
            const toPresent = document.getElementById(
                'yearToPresent'
            ).checked;
            let yt = cy, rangeLabel = '';
            if (toPresent) {
                rangeLabel = yf + '–present';
            } else {
                yt = parseInt(
                    document.getElementById('yearTo').value,10
                );
                if (isNaN(yt)) yt = cy;
                yt = Math.max(1950, Math.min(yt, cy));
                if (yt < yf) { 
                    const t=yt; yt=yf; yf=t; 
                }
                rangeLabel = yf + '–' + yt;
            }
            let qs = 'year_from=' + encodeURIComponent(yf);
            if (toPresent) qs += '&to_present=1';
            else qs += '&year_to=' + encodeURIComponent(yt);

            const output = document.getElementById('output');
            const stepProgress = document.getElementById(
                'stepProgress'
            );
            const progressContainer = document.getElementById(
                'progressContainer'
            );

            progressContainer.style.display = 'none';
            if (stepProgress) stepProgress.style.display='block';

            const stepMsgs = [
                '',
                '🔍 Searching PubMed...',
                '📄 Fetching abstracts...',
                '📚 Fetching PMC full text...',
                '🔓 Unpaywall open access...',
                '⚗️ Extracting & validating data...',
            ];

            function updateSteps(currentStep, message) {
                for (let i = 1; i <= 5; i++) {
                    const el = document.getElementById(
                        'step' + i
                    );
                    const msgEl = document.getElementById(
                        'step' + i + 'msg'
                    );
                    if (!el) continue;
                    if (i < currentStep) {
                        el.className = 'step-row done';
                        if (msgEl) msgEl.textContent = 
                            '✓ ' + stepMsgs[i];
                    } else if (i === currentStep) {
                        el.className = 'step-row active';
                        if (msgEl) msgEl.textContent = 
                            message || stepMsgs[i];
                    } else {
                        el.className = 'step-row waiting';
                        if (msgEl) msgEl.textContent = 
                            stepMsgs[i];
                    }
                }
            }

            updateSteps(1, stepMsgs[1]);
            output.innerHTML = `
                <div style="text-align:center;padding:30px;">
                    <div class="spinner"></div>
                    <h3>Analyzing papers (${rangeLabel})</h3>
                    <p style="color:#aaa;font-size:0.9rem;">
                        Searching PubMed, PMC, and Unpaywall...
                    </p>
                </div>
            `;

            try {
                // Start the job
                const startResp = await fetch(
                    '/api/analyze?' + qs
                );
                const startData = await startResp.json();
                const jobId = startData.job_id;

                if (!jobId) {
                    throw new Error(
                        'No job ID returned from server'
                    );
                }

                // Poll for results
                let pollCount = 0;
                const maxPolls = 300; // 10 min max

                const pollResult = await new Promise(
                    (resolve, reject) => {
                        const interval = setInterval(
                            async () => {
                                pollCount++;
                                if (pollCount > maxPolls) {
                                    clearInterval(interval);
                                    reject(new Error(
                                        'Analysis timed out'
                                    ));
                                    return;
                                }
                                try {
                                    const r = await fetch(
                                        '/api/analyze/result/' 
                                        + jobId
                                    );
                                    const d = await r.json();
                                    
                                    // Update step display
                                    if (d.step) {
                                        updateSteps(
                                            d.step, d.message
                                        );
                                    }

                                    if (d.status === 'complete') {
                                        clearInterval(interval);
                                        // Mark all done
                                        updateSteps(6, '');
                                        resolve(d);
                                    } else if (
                                        d.status === 'error'
                                    ) {
                                        clearInterval(interval);
                                        reject(new Error(
                                            d.message || 
                                            'Analysis failed'
                                        ));
                                    }
                                } catch(e) {
                                    // Network hiccup — 
                                    // keep polling
                                }
                            }, 
                            2000 // Poll every 2 seconds
                        );
                    }
                );

                // Hide steps after delay
                setTimeout(() => {
                    if (stepProgress) 
                        stepProgress.style.display = 'none';
                }, 2000);

                // Update metric cards
                const dispRange = 
                    pollResult.publication_range_label || 
                    rangeLabel;
                document.getElementById(
                    'yearRangeLabel'
                ).textContent = dispRange;
                document.getElementById(
                    'recordsFound'
                ).textContent = pollResult.records_found || 0;
                document.getElementById(
                    'tempCoverage'
                ).textContent = 
                    pollResult.statistics?.temperature_coverage 
                    ?? '0%';
                document.getElementById(
                    'avgConfidence'
                ).textContent = 
                    pollResult.statistics?.average_confidence_pct
                    ?? '0%';
                
                const strainEl = document.getElementById(
                    'strainCoverage'
                );
                if (strainEl) {
                    strainEl.textContent = 
                        pollResult.statistics?.strain_coverage_pct
                        ?? '0%';
                }

                showAnalysisResults(pollResult);
                window._lastAnalysisComparison = 
                    pollResult.comparison || null;

            } catch(error) {
                if (stepProgress) 
                    stepProgress.style.display = 'none';
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
        
        function showAnalysisResults"""

content = frontend_pattern.sub(frontend_replacement, content)


# CHANGE 2, 3, 4 — Backend python changes
backend_pattern = re.compile(
    r'(@app\.get\("/api/analyze"\)\nasync def analyze_papers\(.*?)\n@app\.post\("/api/query"\)',
    re.DOTALL
)

backend_replacement = """async def run_analysis_background(
    job_id: str, 
    yf: int, 
    yt: int, 
    max_results: int,
    range_label: str
):
    \"\"\"Run analysis in background and store result.\"\"\"
    try:
        task_results[job_id] = {
            "status": "running",
            "step": 1,
            "message": "Searching PubMed...",
            "progress": 10,
        }
        
        extractor = ScientificPubMedEColiExtractor()
        
        # Step 1
        pmids, _pmc_map = await _asyncio.to_thread(
            extractor.search_data_rich_papers,
            max_results, yf, yt,
        )
        task_results[job_id].update({
            "step": 2, "progress": 25,
            "message": f"Found {len(pmids)} papers. "
                       f"Fetching abstracts..."
        })
        
        if not pmids:
            task_results[job_id] = {
                "status": "complete",
                "records_found": 0,
                "results": [],
                "statistics": {
                    "key_finding": 
                        f"No papers found for "
                        f"{range_label}.",
                    "temperature_coverage": "0%",
                    "ph_coverage": "0%",
                    "average_confidence_pct": "0%",
                },
                "publication_range_label": range_label,
                "comparison": None,
            }
            return

        # Step 2
        papers_abstract = await _asyncio.to_thread(
            extractor.fetch_paper_data, pmids, False
        )
        task_results[job_id].update({
            "step": 3, "progress": 45,
            "message": f"Got {len(papers_abstract)} "
                       f"abstracts. Fetching PMC..."
        })

        # Step 3 — PMC
        elink_pmc_list = []
        elink_pmid_by_pmc = {}
        if _pmc_map:
            for pid_k, pmcid_v in _pmc_map.items():
                pk = str(pmcid_v).strip()
                if not pk.upper().startswith("PMC"):
                    pk = "PMC" + pk.lstrip("0")
                elink_pmc_list.append(pk)
                elink_pmid_by_pmc[pk.upper()] = str(pid_k)

        pmc_direct_ids = []
        try:
            pmc_direct_ids = await _asyncio.to_thread(
                extractor.search_pmc_directly,
                200, yf, yt,
            )
        except Exception:
            pass

        pmc_direct_pmid_map = {}
        if pmc_direct_ids:
            try:
                pmc_direct_pmid_map = await _asyncio.to_thread(
                    extractor._elink_pmc_to_pubmed,
                    pmc_direct_ids,
                )
            except Exception:
                pass

        combined_pmc = {}
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
                pmc_papers = await _asyncio.to_thread(
                    extractor.fetch_fulltext_pmc,
                    combined_pmc_list,
                    pmid_by_combined_pmc,
                )
            except Exception:
                pass

        task_results[job_id].update({
            "step": 4, "progress": 65,
            "message": f"PMC: {len(pmc_papers)} papers. "
                       f"Running Unpaywall..."
        })

        # Step 4 — Unpaywall
        pmids_with_ft = set(
            str(p.get("pmid", "")) 
            for p in pmc_papers if p.get("pmid")
        )
        pmids_for_unpaywall = [
            p for p in pmids 
            if str(p) not in pmids_with_ft
        ]
        unpaywall_papers = []
        if pmids_for_unpaywall:
            try:
                unpaywall_papers = await _asyncio.to_thread(
                    extractor.fetch_fulltext_unpaywall,
                    pmids_for_unpaywall,
                )
            except Exception:
                pass

        all_fulltext = pmc_papers + unpaywall_papers
        
        if all_fulltext:
            merged_papers = await _asyncio.to_thread(
                extractor.merge_abstract_and_fulltext,
                papers_abstract, all_fulltext,
            )
        else:
            merged_papers = papers_abstract

        task_results[job_id].update({
            "step": 5, "progress": 85,
            "message": f"Extracting data from "
                       f"{len(merged_papers)} papers..."
        })

        # Step 5 — Extract
        structured_data = await _asyncio.to_thread(
            extractor.extract_structured_data,
            merged_papers
        )

        n = len(structured_data)
        
        # Calculate all statistics 
        # (same logic as existing /api/analyze)
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
            if r.get('strain') and (
                r['strain'].get('name')
                if isinstance(r['strain'], dict)
                else r['strain']
            ) not in (None, '', 'Unknown')
        )

        temp_pct = (temp_count/n*100) if n else 0
        ph_pct = (ph_count/n*100) if n else 0
        avg_yield = round(
            sum(yield_values)/len(yield_values), 3
        ) if yield_values else 0
        avg_conf = round(
            sum(confidence_values)/len(confidence_values)*100
        ) if confidence_values else 0
        strain_pct = (strain_count/n*100) if n else 0

        abs_records = [
            r for r in structured_data 
            if r.get("data_source") != "pmc_fulltext"
        ]
        ft_records = [
            r for r in structured_data 
            if r.get("data_source") == "pmc_fulltext"
        ]

        def _pct_str(c, t):
            return "0%" if t == 0 \
                else f"{c/t*100:.1f}%"
        def _hv(rec, key):
            v = rec.get(key)
            if not v: return False
            if isinstance(v, dict): 
                return bool(v.get("value"))
            return True

        comparison = {
            "abstract_records": len(abs_records),
            "fulltext_records": len(ft_records),
            "abstract": {
                "strain_name": _pct_str(
                    sum(1 for r in abs_records 
                        if r.get('strain') and
                        (r['strain'].get('name') 
                         if isinstance(r['strain'],dict) 
                         else r['strain']) 
                        not in (None,'','Unknown')),
                    len(abs_records)
                ),
                "temperature": _pct_str(
                    sum(1 for r in abs_records 
                        if _hv(r,"temperature")),
                    len(abs_records)
                ),
                "ph": _pct_str(
                    sum(1 for r in abs_records 
                        if _hv(r,"ph")),
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
                    sum(1 for r in ft_records 
                        if r.get('strain') and
                        (r['strain'].get('name') 
                         if isinstance(r['strain'],dict) 
                         else r['strain']) 
                        not in (None,'','Unknown')),
                    len(ft_records)
                ),
                "temperature": _pct_str(
                    sum(1 for r in ft_records 
                        if _hv(r,"temperature")),
                    len(ft_records)
                ),
                "ph": _pct_str(
                    sum(1 for r in ft_records 
                        if _hv(r,"ph")),
                    len(ft_records)
                ),
                "yield": _pct_str(
                    sum(1 for r in ft_records 
                        if r.get("yield_value")),
                    len(ft_records)
                ),
            },
            "pmc_fetch": getattr(
                extractor, "_pmc_fetch_summary",
                {"success":0,"failed":0,"fallback":0}
            ),
        }

        year_distribution = {}
        for r in structured_data:
            yr = str(r.get('year',''))[:4]
            if yr.isdigit() and 1990<=int(yr)<=2030:
                year_distribution[yr] = (
                    year_distribution.get(yr,0)+1
                )
        year_distribution = dict(
            sorted(year_distribution.items())
        )

        results_for_frontend = _transform_to_api_format(
            structured_data
        )
        
        def count_filled(rec):
            fields = [
                rec.get('strain'),
                rec.get('temperature'),
                rec.get('ph'),
                rec.get('yield_value'),
                rec.get('medium'),
            ]
            return sum(1 for f in fields 
                       if f is not None and f != '')
        
        results_sorted = sorted(
            results_for_frontend,
            key=count_filled, reverse=True
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
        analyses[timestamp] = {
            "id": timestamp,
            "results": results_for_frontend,
            "timestamp": datetime.now().isoformat(),
        }

        import json as _json, csv as _csv
        with open(
            f"ecoli_dataset_{timestamp}.json",
            "w", encoding="utf-8"
        ) as f:
            _json.dump(structured_data, f, indent=2)
        
        flat = _flatten_for_csv(structured_data)
        if flat:
            with open(
                f"ecoli_dataset_{timestamp}.csv",
                "w", newline="", encoding="utf-8"
            ) as f:
                w = _csv.DictWriter(
                    f, fieldnames=flat[0].keys()
                )
                w.writeheader()
                w.writerows(flat)

        task_results[job_id] = {
            "status": "complete",
            "analysis_id": timestamp,
            "records_found": n,
            "results": results_sorted[:10],
            "year_from": yf,
            "year_to": yt,
            "publication_range_label": range_label,
            "statistics": {
                "temperature_coverage": 
                    f"{temp_pct:.1f}%",
                "ph_coverage": 
                    f"{ph_pct:.1f}%",
                "average_yield": avg_yield,
                "average_confidence": avg_conf,
                "avg_confidence": f"{avg_conf}%",
                "temp_coverage_pct": 
                    f"{temp_pct:.0f}%",
                "ph_coverage_pct": 
                    f"{ph_pct:.0f}%",
                "average_confidence_pct": 
                    f"{avg_conf}%",
                "strain_coverage": 
                    f"{strain_pct:.1f}%",
                "strain_coverage_pct": 
                    f"{strain_pct:.0f}%",
                "key_finding": (
                    f"Range {range_label}: "
                    f"extracted {n} records. "
                    f"Fulltext: PMC "
                    f"{len(pmc_papers)}, "
                    f"Unpaywall "
                    f"{len(unpaywall_papers)}. "
                    + (f"Only {temp_pct:.0f}% "
                       f"report temperature!"
                       if n else "")
                ),
            },
            "comparison": comparison,
            "year_distribution": year_distribution,
            "pmc_direct_found": len(pmc_direct_ids),
            "pmc_fulltext_fetched": len(pmc_papers),
            "progress": 100,
            "step": 5,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        task_results[job_id] = {
            "status": "error",
            "message": str(e),
            "progress": 0,
        }

@app.get("/api/analyze")
async def analyze_papers(
    year_from: int = 2020,
    year_to: Optional[int] = None,
    to_present: bool = False,
    max_results: int = 500,
):
    \"\"\"Start analysis as background task, 
    return job_id immediately.\"\"\"
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

    import uuid
    job_id = (
        datetime.now().strftime("%Y%m%d_%H%M%S") 
        + "_" + str(uuid.uuid4())[:8]
    )

    task_results[job_id] = {
        "status": "running",
        "step": 1,
        "progress": 5,
        "message": "Starting analysis...",
    }

    # Start background task
    _asyncio.create_task(
        run_analysis_background(
            job_id, yf, yt, max_results, range_label
        )
    )

    return {
        "status": "started",
        "job_id": job_id,
        "message": (
            f"Analysis started for {range_label}. "
            f"Poll /api/analyze/result/{job_id}"
        ),
    }

@app.get("/api/analyze/result/{job_id}")
async def get_analysis_result(job_id: str):
    \"\"\"Poll for analysis job status and results.\"\"\"
    result = task_results.get(job_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )
    return result

@app.post("/api/query")"""

content = backend_pattern.sub(backend_replacement, content)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
