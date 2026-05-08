$(document).ready(function () {

    // =========================================
    // 側邊欄目錄
    // =========================================
    const $apiContent = $('.api-editer');
    const $tocList = $('.right-directory ul');
    let idCounter = 1;

    $apiContent.find('.sec_title h3, .green_title h4').each(function () {
        const $el = $(this);
        const text = $el.text().trim();
        const isSub = $el.is('h4');
        let id;

        if (isSub) {
            id = $el.attr('id') || ('api-anchor-' + idCounter++);
            $el.attr('id', id);
        } else {
            const $section = $el.closest('.item_one');
            id = $section.attr('id') || ('api-anchor-' + idCounter++);
            $section.attr('id', id);
        }

        const $a = $('<a href="#"></a>')
            .addClass(isSub ? 's-title' : 'b-title')
            .append(isSub ? $('<h3></h3>').text(text) : $('<h2></h2>').text(text))
            .on('click', function (e) {
                e.preventDefault();
                const w = $(window).width();
                const offset = w <= 999 ? 65 : (w <= 1599 ? 85 : 105);
                $('html, body').animate({
                    scrollTop: $('#' + id).offset().top - offset
                }, 400);
            });

        $('<li></li>').append($a).appendTo($tocList);
    });

    if ($tocList.find('li').length === 0) {
        $('.right-directory').remove();
    }

    $('.mb-cbtn').on('click', function () {
        $(this).toggleClass('active');
        $('.right-directory ul').slideToggle();
    });

    $(window).on('resize', function () {
        if ($(window).width() > 768) {
            $('.right-directory ul').show();
        } else if (!$('.mb-cbtn').hasClass('active')) {
            $('.right-directory ul').hide();
        }
    }).trigger('resize');


    // =========================================
    // 視覺強化
    // =========================================

    // 型值 badge（含 float）
    $('.api-editer table.table_style2 td').each(function () {
        const $td = $(this);
        if ($td.children().length > 0) return;
        const t = $td.text().trim();
        if (['string', 'integer', 'boolean', 'date', 'number', 'float'].includes(t)) {
            $td.html('<span class="type-badge type-' + t + '">' + t + '</span>');
        }
    });

    // 狀態碼配色
    $('.api-editer table.table_style2 tr').each(function () {
        const $td = $(this).children('td').first();
        const code = $td.text().trim();
        if (/^\d{3}$/.test(code)) {
            let cls = 'status-2xx';
            if (code[0] === '4') cls = 'status-4xx';
            else if (code[0] === '5') cls = 'status-5xx';
            $td.html('<span class="status-code ' + cls + '">' + code + '</span>');
        }
    });

    // 格式 inline code
    $('.api-editer table.table_style2 tr:gt(0) td:nth-child(3)').each(function () {
        const $td = $(this);
        let html = $td.html();
        if (!html) return;
        const before = html;
        html = html.replace(/(輸入值=(?:\{[^}]+\},?)+)/g,
            '<code class="inline-code">$1</code>');
        html = html.replace(/(?:日期格式|年份格式)：([a-z-]+)/gi,
            function (m, fmt) {
                return m.replace(fmt, '<code class="inline-code">' + fmt + '</code>');
            });
        if (html !== before) $td.html(html);
    });

    // 色塊（用 class，不用 inline style）
    const swatchMap = {
        '#ffffcc': 1, '#ffeda0': 2, '#fed976': 3, '#feb24c': 4,
        '#fd8d3c': 5, '#fc4e2a': 6, '#e31a1c': 7, '#bd0026': 8
    };
    $('.api-editer table.table_style2 td').each(function () {
        const $td = $(this);
        if ($td.children().length > 0) return;
        const t = $td.text().trim().toLowerCase();
        if (swatchMap[t]) {
            $td.html(
                '<span class="color-swatch swatch-' + swatchMap[t] + '"></span>' +
                '<span class="color-hex">' + t + '</span>'
            );
        }
    });


    // JSON：先 dedent 再高亮
    $('.api-editer .gray-box pre code').each(function () {
        const $code = $(this);
        const raw = $code.text();
        const lines = raw.split('\n');

        // 跳過第一行算最小縮排（第一行通常緊貼 <code> 沒縮排）
        let minIndent = Infinity;
        for (let i = 1; i < lines.length; i++) {
            if (!lines[i].trim()) continue;
            const m = lines[i].match(/^[ \t]*/);
            if (m) minIndent = Math.min(minIndent, m[0].length);
        }

        if (minIndent > 0 && minIndent !== Infinity) {
            const re = new RegExp('^[ \\t]{0,' + minIndent + '}');
            const dedented = lines.map(function (line, i) {
                return i === 0 ? line : line.replace(re, '');
            }).join('\n');
            $code.text(dedented);
        }

        let html = $code.html();
        html = html.replace(/"([^"]+)"(\s*:)/g, '<span class="j-key">"$1"</span>$2');
        html = html.replace(/:(\s*)([\u4e00-\u9fa5][^\n,]*)/g,
            ': <span class="j-comment">$2</span>');
        $code.html(html);
    });



    // 「支援區間查詢」「控制詞彙」變錨點
    $('.api-editer table.table_style2 td').each(function () {
        const $td = $(this);
        let html = $td.html();
        if (!html) return;
        const before = html;
        html = html.replace(/可複合查詢/g,
            '可<a class="col_blue" href="#composite-query-area">複合查詢</a>');
        html = html.replace(/支援區間查詢/g,
            '支援<a class="col_blue" href="#range-query-area">區間查詢</a>');
        html = html.replace(/請見控制詞彙列表/g,
            '請見<a class="col_blue" href="#vocab-area">控制詞彙列表</a>');        
        if (html !== before) $td.html(html);
    });

});