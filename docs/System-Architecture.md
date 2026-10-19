# ISTMOSAR — System Architecture v1.0
Owner: José Peñalba | Status: conceptual, not competition implementation

## Pipeline
Official ASF Vertex / NASA Earthdata Search (traceable granules) -> Harmony individual GCOV GeoTIFF extraction OR HDF5 via h5py/earthaccess -> QGIS scientific inspection -> separate Python raster processing (rasterio, numpy; GDAL optional) -> projected aligned clipped masked GeoTIFF, change image and stats + provenance JSON -> FastAPI static output / metadata endpoints + optional SQLite -> React/Vite + Leaflet + Chart.js.

## Boundaries
Research and dataset selection occur before development subject to competition rules. Challenge-specific code and integration are built only when authorized. No API key in browser; credentials via secure environment if needed. Raw large scenes not committed to Git. Preprocess once, serve compact map-ready outputs; don't recompute full scene on every request.

## Modules
- Catalog/manifest: source, granule ID, collection, acquisition time, orbit/frame, footprint, polarization, mode, processing version, relevant licensing.
- Scientific processing: verified comparable pair, reference grid, QA/nodata, backscatter units, method, parameters, output rasters, QC log.
- API: GET /api/study-areas ; GET /api/scenes ; GET /api/analyses ; GET /api/analyses/{id} ; GET /api/analyses/{id}/layers ; GET /health.
- UI: study area, scene list, before/after toggle/slider, change layer/legend, statistics and limitations panel.
- Optional adapters: wetland classifier, environmental sensor API, GUNW processor, soil moisture, etc. These are not MVP dependencies.

## API sample contract (design proposal)
An analysis object: id, area_id, scenes[2], product, channel, method, parameters, dates, raster_url, statistics, limitations, citations, processing_version. Never infer a flood event purely from change magnitude.

## Scientific transformation
For positive finite diagonal GCOV backscatter power: B_dB = 10 log10(gamma0). Compare aligned grids: delta_dB = B2_dB - B1_dB. Mask invalid pixels and document any smoothing, clipping, reprojection and class thresholds. Check product known issues and versions. Preserve units and uncertainty.

## Risks and mitigations
1. No suitable Panama pair: widen search area/date then pivot using verified data evidence.
2. No Harmony spatial clipping: extract layer, crop locally; do not rely on roadmap service.
3. Large files / laptop limits: small AOI, optimized GeoTIFF, offline assets.
4. Science overclaim: intensity-change labels, evidence, explicit uncertainty.
5. Frontend/backend integration: frozen JSON schema and sample fixtures for learning; event-specific implementation subject to challenge rules.
6. Connectivity: serve precomputed outputs locally and retain video backup.
7. InSAR branch complexity: separate pipeline with explicit entry criteria.
