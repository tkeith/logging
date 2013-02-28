apiPrefix = './api/'

username = null
password = null

tags = []
params = []

searchAfterLogin = false

addBlankTagInput = ->
  return $('#templates .tag-input-line').clone(true).appendTo($('#tag-inputs'))

addBlankParamInput = ->
  return $('#templates .param-input-line').clone(true).
                                                    appendTo($('#param-inputs'))

tagInputBlank = (line) -> line.find('.tag-input').val() == ''

paramInputBlank = (line) -> line.find('.key-input').val() == '' and \
                                           line.find('.value-input').val() == ''

refreshInputs = ->
  lastTag = $('#search-form .tag-input-line:last')
  lastParam = $('#search-form .param-input-line:last')
  if lastTag.length == 0 or not tagInputBlank(lastTag)
    lastTag = addBlankTagInput()
  if lastParam.length == 0 or not paramInputBlank(lastParam)
    lastParam = addBlankParamInput()
  $('#search-form .tag-input-line').each ->
    el = $(this)
    if this != lastTag[0] and tagInputBlank(el)
      el.remove()
  $('#search-form .param-input-line').each ->
    el = $(this)
    if this != lastParam[0] and paramInputBlank(el)
      el.remove()

renderSearchInputs = ->
  tagInputs = $('#tag-inputs')
  paramInputs = $('#param-inputs')
  tagInputs.html('')
  paramInputs.html('')
  for tag in tags
    el = $('#templates .tag-input-line').clone()
    el.find('.tag-input').val(tag)
    tagInputs.append(el)
  for param in params
    el = $('#templates .param-input-line').clone()
    el.find('.key-input').val(param[0])
    el.find('.value-input').val(param[1])
    paramInputs.append(el)
  refreshInputs()

loadInputs = (search) ->
  search = $.parseJSON(search)
  tags = search.tags
  params = search.params
  renderSearchInputs()

api = (params) ->
  params.url = apiPrefix + params.url
  params.username = username
  params.password = password
  $.ajax(params)

renderLogs = (logs, container) ->
  container.html('')
  $.each logs, (index, log) ->
    logEl = $('#templates .log').clone()
    logEl.find('.time').text(log.time)
    $.each log.tags, (index, tag) ->
      tagEl = $('#templates .tag').clone()
      tagEl.text(tag)
      tagEl.appendTo(logEl.find('.tags'))
    $.each log.params, (key, value) ->
      paramEl = $('#templates .param').clone()
      paramEl.find('.key').text(key)
      paramEl.find('.value').text(value)
      paramEl.appendTo(logEl.find('.params'))
    if log.num_children > 0
      showChCont = logEl.find('.show-children-container')
      showChCont.show()
      logEl.find('.show-children').on 'click', ->
        showChCont.hide()
        childrenEl = logEl.find('.children')
        childrenEl.show()
        api
          url: 'logs/' + log.id + '/children/'
          success: (data) ->
            logs = data.logs
            renderLogs(logs, childrenEl)
        return false
    container.append(logEl)

doSearch = ->
  apiParams = {}
  $.each params, (index, param) ->
    apiParams[param[0]] = param[1]
  api
    url: 'logs/'
    data:
      tags: JSON.stringify(tags)
      params: JSON.stringify(apiParams)
    success: (data) ->
      logs = data.logs
      renderLogs(logs, $('#logs'))

class Router extends Backbone.Router
  routes:
    'search/*data': 'search'
    '': 'index'

  index: renderSearchInputs

  search: (search) ->
    loadInputs(unescape(search))
    if username != null
      doSearch()
    else
      searchAfterLogin = true

router = new Router()

Backbone.history.start()

testLoginInfo = (params) ->
  $.ajax
    url: apiPrefix + 'users/'
    data: {username: username, password: password}
    success: params.success
    error: params.error

showLogin = ->
  $('#login-modal').modal('show')

$ ->
  $('.search-input').on 'input', ->
    refreshInputs()

  $('#search-form').on 'submit', ->
    tags = []
    params = []
    $('#search-form .tag-input-line').each ->
      el = $(this)
      if not tagInputBlank(el)
        tags.push(el.find('.tag-input').val())
    $('#search-form .param-input-line').each ->
      el = $(this)
      if not paramInputBlank(el)
        params.push [
          el.find('.key-input').val()
          el.find('.value-input').val()
        ]
    search = {tags: tags, params: params}
    router.navigate('search/' + escape(JSON.stringify(search)))
    doSearch()
    return false

  $('#login-form').on 'submit', ->
    $('#login-error').hide()
    username = $('#login-username-input').val()
    password = $('#login-password-input').val()
    testLoginInfo
      success: ->
        if $('#save-password').is(':checked')
          $.cookie('username', username, {expires: 3650})
          $.cookie('password', password, {expires: 3650})
        $('#login-modal').modal('hide')
        if searchAfterLogin
          doSearch()
      error: ->
        $('#login-error').show()
    return false

  username = $.cookie('username')
  password = $.cookie('password')
  if not (username and password)
    showLogin()
  else
    testLoginInfo
      success: ->
        if searchAfterLogin
          doSearch()
      error: ->
        showLogin()
