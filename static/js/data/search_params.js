// 網站搜尋參數 v2（3.4，D20）：表單欄位 ↔ 網址參數
// 網址、送給後端、存進資料庫的參數一律是 v2（與 API 相同）；表單上有幾個欄位仍用舊的組合方式，在這裡轉換：
//   has_image（多選下拉）     ↔ hasMedia + mediaType
//   start_date / end_date     ↔ eventDate=YYYYMMDD,YYYYMMDD（一邊可為 *）
//   geo_type + 圓心 / 半徑     ↔ circle=經度,緯度,半徑；geo_type=map ↔ polygon；geo_type=polygon ↔ geojson_id
// 後端的對照在 data/search_params.py（舊網址由後端轉址成 v2，前端只需處理表單）

const MEDIA_TYPES = ['image', 'video', 'audio']

// 表單送出的參數（URL query string）→ v2
function formToV2(queryString) {
    const p = new URLSearchParams(queryString)
    const out = new URLSearchParams()
    const geoType = p.get('geo_type')
    const skip = new Set(['has_image', 'start_date', 'end_date', 'geo_type', 'center_lon', 'center_lat', 'circle_radius'])
    for (const [k, v] of p.entries()) {
        if (skip.has(k)) continue
        if (k === 'polygon' && geoType !== 'map') continue
        if (k === 'geojson_id' && geoType !== 'polygon') continue
        out.append(k, v)
    }
    // 多媒體：無多媒體 → hasMedia=false；三種類型全選（或舊值 y）→ hasMedia=true；部分類型 → hasMedia=true + mediaType（可多個）
    const media = p.getAll('has_image')
    const types = MEDIA_TYPES.filter(t => media.includes(t))
    if (media.includes('n')) {
        out.set('hasMedia', 'false')
    } else if (media.includes('y') || types.length === MEDIA_TYPES.length) {
        out.set('hasMedia', 'true')
    } else if (types.length > 0) {
        out.set('hasMedia', 'true')
        types.forEach(t => out.append('mediaType', t))
    }
    // 日期 YYYY-MM-DD → YYYYMMDD
    const d8 = (v) => (v || '').trim().replace(/-/g, '')
    const s = d8(p.get('start_date')), e = d8(p.get('end_date'))
    if (s || e) {
        out.set('eventDate', (s && e && s === e) ? s : `${s || '*'},${e || '*'}`)
    }
    // 圓形範圍
    if (geoType === 'circle' && p.get('center_lon') && p.get('center_lat') && p.get('circle_radius')) {
        out.set('circle', [p.get('center_lon'), p.get('center_lat'), p.get('circle_radius')].map(x => x.trim()).join(','))
    }
    return out.toString()
}

// v2 網址參數 → 表單欄位（頁面載入時還原條件用；回傳 URLSearchParams）
function v2ToForm(urlParams) {
    const out = new URLSearchParams()
    for (const [k, v] of urlParams.entries()) {
        if (['hasMedia', 'mediaType', 'eventDate', 'circle'].includes(k)) continue
        out.append(k, v)
    }
    const hasMedia = urlParams.get('hasMedia')
    if (hasMedia === 'false') {
        out.set('has_image', 'n')
    } else if (hasMedia === 'true') {
        // 沒有指定類型 = 三種都選；mediaType 可能是重複參數或半形逗號
        let types = urlParams.getAll('mediaType').flatMap(v => v.split(',')).filter(t => MEDIA_TYPES.includes(t))
        if (types.length === 0) types = MEDIA_TYPES
        types.forEach(t => out.append('has_image', t))
    }
    const ymd = (v) => (/^\d{8}$/.test(v) ? `${v.slice(0, 4)}-${v.slice(4, 6)}-${v.slice(6)}` : '')
    const ev = urlParams.get('eventDate')
    if (ev) {
        const [s, e] = ev.includes(',') ? ev.split(',') : [ev, ev]
        if (ymd(s)) out.set('start_date', ymd(s))
        if (ymd(e)) out.set('end_date', ymd(e))
    }
    const circle = urlParams.get('circle')
    if (circle && circle.split(',').length === 3) {
        const [lon, lat, r] = circle.split(',')
        out.set('geo_type', 'circle')
        out.set('center_lon', lon)
        out.set('center_lat', lat)
        out.set('circle_radius', r)
    } else if (urlParams.getAll('polygon').length > 0) {
        out.set('geo_type', 'map')
    } else if (urlParams.get('geojson_id')) {
        out.set('geo_type', 'polygon')
    }
    return out
}

// 圓形範圍半徑上限（公里，同 API）
const CIRCLE_MAX_KM = 25
