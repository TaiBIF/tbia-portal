var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

$( function() {
    // default active page
    if (($('input[name=resource_type]').val() != 'all' ) & ($('input[name=resource_type]').val() != '' )) {
        $('.news_tab_in li').removeClass('now');
        $(`#${$('input[name=resource_type]').val()}`).addClass('now');
        $('#db-intro').addClass('d-none')
    } 

    $('.changePage').on('click', function(){
        changePage($(this).data('page'), $(this).data('type'))
    })

    $('.show_start').on('click', function(){
        $('#start_date').datepicker('show')
    })

    $('.show_end').on('click', function(){
        $('#end_date').datepicker('show')
    })

	$("#start_date").datepicker({ dateFormat: 'yy-mm-dd' });
	$("#end_date").datepicker({ dateFormat: 'yy-mm-dd' });
});

$('.news_tab_in li').click(function(){
	let li_element = $(this)
	let type = this.id
    $.ajax({
        url: "/get_resources",
        data: {
          type: type,
          from: 'resource',
          get_page: 1,
          csrfmiddlewaretoken: $csrf_token,
        },
        type: 'POST',
        dataType : 'json',
    })
    .done(function(response) {
      // change active tab
      $('.news_tab_in li').removeClass('now');
      li_element.addClass('now');
	  if (type == 'all'){
		$('#db-intro').removeClass('d-none')
		window.history.pushState('page', 'Title', '/resources')
	  } else {
		$('#db-intro').addClass('d-none')
		window.history.pushState('page', 'Title', `/resources?type=${type}`)
	}
	  // remove all resources first
      $('.edu_list li').remove()
      $(`.page_number`).remove()
      // append rows
      if (response.rows.length > 0){
        for (let i = 0; i < response.rows.length; i++) {
			$('.edu_list').append(`
			<li>
			  <div class="item">
				<div class="cate_dbox">
				  <div class="cate ${response.rows[i].cate}">${response.rows[i].extension}</div>
				  <div class="date">${response.rows[i].date}</div>
				</div>
				<a href="/static/${response.rows[i].url}" class="title" target="_blank">${response.rows[i].title}</a>
				<a href="/static/${response.rows[i].url}" download class="dow_btn"> </a>
			  </div>
			</li>`)  
        }
      } else {
	  $('.edu_list').append(`<li>
		<div class="item">
		  <div class="cate_dbox">
			<div class="cate other color-888">-----</div>
			<div class="date">2000.5.22</div>
		  </div>
		  <a class="title">更新中</a>
		</div>
	  </li>`)
	  }

        // 修改頁碼
        $('.edu_list').after(`<div class="page_number"></div>`)
        if (response.page_list.length > 1){  // 判斷是否有下一頁，有才加分頁按鈕
            $(`.page_number`).append(
                `
                <a href="javascript:;" class="num changePage" data-page="1" data-type="resource">1</a>
                <a href="javascript:;" class="pre">上一頁</a>  
                <a href="javascript:;" class="next">下一頁</a>
                <a href="javascript:;" class="num changePage" data-page="${response.total_page}" data-type="resource">${response.total_page}</a>
            `)
        }		
            
        if (response.page_list.includes(response.current_page-1)){
            $('.pre').addClass('changePage')
            $('.pre').data('page', response.current_page-1)
            $('.pre').data('type', type)
        } else {
            $('.pre').addClass('pt-none')
        }

        let html = ''
        for (let i = 0; i < response.page_list.length; i++) {
            if (response.page_list[i] == response.current_page){
            html += ` <a href="javascript:;" class="num now changePage" data-page="${response.page_list[i]}" data-type="resource">${response.page_list[i]}</a>  `;
            } else {
            html += ` <a href="javascript:;" class="num changePage" data-page="${response.page_list[i]}" data-type="resource">${response.page_list[i]}</a>  `
            }
        }

        $('.pre').after(html)

        // 如果有下一頁，改掉next的onclick
        if (response.current_page < response.total_page){
            $('.next').addClass('changePage')
            $('.next').data('page', response.current_page+1)
            $('.next').data('type', type)
        } else {
            $('.next').addClass('pt-none')
        }  

        $('.changePage').off('click')
        $('.changePage').on('click', function(){
            changePage($(this).data('page'), $(this).data('type'))
        })
	})
    .fail(function( xhr, status, errorThrown ) {
      alert('發生未知錯誤！請聯絡管理員')
      console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
    })
  })

  $('.date_select .search_btn').click(function(){
	$('#db-intro').addClass('d-none')
	$.ajax({
        url: "/get_resources",
        data: {
          type: $('.news_tab_in li.now').prop('id'),
          from: 'resource',
          start_date: $("#start_date").val(),
          end_date: $("#end_date").val(),
          csrfmiddlewaretoken: $csrf_token,
        },
        type: 'POST',
        dataType : 'json',
    })
    .done(function(response) {
	  // remove all resources first
      $('.edu_list li').remove()
      $('.page_number').remove()
      // append rows
      if (response.rows.length > 0){
        for (let i = 0; i < response.rows.length; i++) {
			$('.edu_list').append(`
			<li>
			  <div class="item">
				<div class="cate_dbox">
				  <div class="cate ${response.rows[i].cate}">${response.rows[i].extension}</div>
				  <div class="date">${response.rows[i].date}</div>
				</div>
				<a href="/static/${response.rows[i].url}" class="title" target="_blank">${response.rows[i].title}</a>
				<a href="/static/${response.rows[i].url}" download class="dow_btn"> </a>
			  </div>
			</li>`)  
        }

        $('.edu_list').after(`<div class="page_number"></div>`)

          // 修改頁碼
          if (response.page_list.length > 1){  // 判斷是否有下一頁，有才加分頁按鈕
              $(`.page_number`).append(
                `
                  <a href="javascript:;" class="num changePage" data-page="1" data-type="search">1</a>
                  <a href="javascript:;" class="pre">上一頁</a>  
                  <a href="javascript:;" class="next">下一頁</a>
                  <a href="javascript:;" class="num changePage" data-page="${response.total_page}" data-type="search">${response.total_page}</a>
              `)
          }		
            
          if (response.page_list.includes(response.current_page-1)){
            $('.pre').addClass('changePage')
            $('.pre').data('page', response.current_page-1)
            $('.pre').data('type', 'search')
          } else {
            $('.pre').addClass('pt-none')
          }

          let html = ''
          for (let i = 0; i < response.page_list.length; i++) {
            if (response.page_list[i] == response.current_page){
              html += ` <a href="javascript:;" class="num now changePage" data-page="${response.page_list[i]}" data-type="search">${response.page_list[i]}</a>  `;
            } else {
              html += ` <a href="javascript:;" class="num changePage" data-page="${response.page_list[i]}" data-type="search">${response.page_list[i]}</a>  `
            }
          }

          $('.pre').after(html)
  
          // 如果有下一頁，改掉next的onclick
          if (response.current_page < response.total_page){
            $('.next').addClass('changePage')
            $('.next').data('page', response.current_page+1)
            $('.next').data('type', 'search')
          } else {
            $('.next').addClass('pt-none')
          }  

          $('.changePage').on('click', function(){
            changePage($(this).data('page'), $(this).data('type'))
          })

      } else {
        // if no row, show '更新中'
        $('.edu_list').append(`
        <li>
            <div class="item no_data bd-0">
            <a class="title">查無資料</a>
            </div>
        </li>`)
	  }
    })
    .fail(function( xhr, status, errorThrown ) {
      alert('發生未知錯誤！請聯絡管理員')
      console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
    })
  })

function changePage (page, by){

  // 如果是從search，要把日期篩選也算進去
  let start_date, end_date
  if (by == 'search'){
    start_date = $("#start_date").val()
    end_date = $("#end_date").val()
  } 

  if ($('.news_tab_in li.now').prop('id') == 'all'){
    if (page >1) {
      $('#db-intro').addClass('d-none')
    } else  {
      $('#db-intro').removeClass('d-none')
    }
  }

  $.ajax({
        url: "/get_resources",
        data: {
          type: $('.news_tab_in li.now').prop('id'),
          from: 'resource',
          start_date: start_date,
          end_date: end_date,
          csrfmiddlewaretoken: $csrf_token,
          get_page: page
        },
        type: 'POST',
        dataType : 'json',
    })
    .done(function(response) {
    // remove all resources first
      $('.edu_list li').remove()
      $('.page_number').remove()
      // append rows
      if (response.rows.length > 0){
        for (let i = 0; i < response.rows.length; i++) {
          $('.edu_list').append(`
          <li>
            <div class="item">
            <div class="cate_dbox">
              <div class="cate ${response.rows[i].cate}">${response.rows[i].extension}</div>
              <div class="date">${response.rows[i].date}</div>
            </div>
            <a href="/static/${response.rows[i].url}" class="title" target="_blank">${response.rows[i].title}</a>
            <a href="/static/${response.rows[i].url}" download class="dow_btn"> </a>
            </div>
          </li>`)  
        }
      } else {
          // if no row, show '更新中'
        $('.edu_list').append(`<li>
        <div class="item no_data bd-0">
          <a class="title">查無資料</a>
        </div>
        </li>`)
      }

      $('.edu_list').after(`<div class="page_number"></div>`)

        // 修改頁碼
        if (response.page_list.length > 1){  // 判斷是否有下一頁，有才加分頁按鈕
          $(`.page_number`).append(
            `
              <a href="javascript:;" class="num changePage" data-page="1" data-type="${by}">1</a>
              <a href="javascript:;" class="pre">上一頁</a>  
              <a href="javascript:;" class="next">下一頁</a>
              <a href="javascript:;" class="num changePage" data-page="${response.total_page}" data-type="${by}">${response.total_page}</a>
          `)
        }		
          
        if (response.page_list.includes(response.current_page-1)){
          $('.pre').addClass('changePage')
          $('.pre').data('page', response.current_page-1)
          $('.pre').data('type', by)
        } else {
          $('.pre').addClass('pt-none')
        }

        let html = ''
        for (let i = 0; i < response.page_list.length; i++) {
          if (response.page_list[i] == response.current_page){
            html += ` <a href="javascript:;" class="num now changePage" data-page="${response.page_list[i]}" data-type="${by}">${response.page_list[i]}</a>  `;
          } else {
            html += ` <a href="javascript:;" class="num changePage" data-page="${response.page_list[i]}" data-type="${by}">${response.page_list[i]}</a>  `
          }
        }

        $('.pre').after(html)

        // 如果有下一頁，改掉next的onclick
        if (response.current_page < response.total_page){
          $('.next').addClass('changePage')
          $('.next').data('page', response.current_page+1)
          $('.next').data('type', by)
        } else {
          $('.next').addClass('pt-none')
        }  

        $('.changePage').off('click')
        $('.changePage').on('click', function(){
          changePage($(this).data('page'), $(this).data('type'))
        })

    })
    .fail(function( xhr, status, errorThrown ) {
      alert('發生未知錯誤！請聯絡管理員')
      console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
    })

}

