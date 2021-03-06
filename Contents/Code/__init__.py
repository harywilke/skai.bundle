#TITLE = 'ΣΚΑΪ'
TITLE = "SKAI"
PREFIX = "/video/skai"

ICON = "icon-default.png"
ART = "art-default.jpg"

BASE_URL = "http://www.skai.gr"
BASE_TV_PLAYER_URL = BASE_URL + "/player/"
LIVE_TV_URL = BASE_TV_PLAYER_URL + "tvlive/"

RE_EPISODE_ID = Regex('(\d+)')


####################################################################################################
def Start():
  Log("skai start ()")
  ObjectContainer.title1 = TITLE
  ObjectContainer.art = R(ART)
  DirectoryObject.thumb = R(ICON)
  EpisodeObject.thumb = R(ICON)

  #HTTP.CacheTime = CACHE_1HOUR
  #HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36'
####################################################################################################
@handler(PREFIX, TITLE, thumb = ICON, art = ART)
def MainMenu():
  Log("MainMenu ()")
  oc = ObjectContainer(title1 = TITLE)
  html = HTML.ElementFromURL(LIVE_TV_URL)
  categories = html.xpath('//*[@class=" first"]')
  for category in categories:
    category_title = category.xpath('./a/text()')[0]
    category_id = category.xpath('./@id')[0] 
    Log('got a category id : %s' % category_id)
    Log('got a category:' + category_title)
    Log('****')
    #shows = category.xpath("//*[contains(@href,'loaditemscatlist')]")
    #Log(shows)
    #Log(category.xpath("//*[contains(@href,'loaditemscatlist')]/text()"))
    oc.add(DirectoryObject(key = Callback(CategoriesMenu, title = category_title, category = category_id), title = category_title))

  return oc

####################################################################################################
@route(PREFIX + '/CategoriesMenu', title=str, category=str)
def CategoriesMenu(title, category):
  Log('CategoriesMenu -> category : %s' % category)
  oc = ObjectContainer(title1 = title)
  html = HTML.ElementFromURL(LIVE_TV_URL)
  #shows = html.xpath('//*[@id=%s]/a/text()' % category)
    
  shows = html.xpath('//*[@class=" first" and @id=%s]//*[contains(@href,"loaditemscatlist")]/..' % category)
  Log('CategoriesMenu -> shows: %s' % shows)
  for show in shows:
    show_id = show.xpath('./@id')
    show_title = show.xpath('.//a/text()')[0]
    Log('CategoriesMenu -> show_id: %s' % show_id)
    Log('CategoriesMenu -> show_name: %s' % show_title)
    oc.add(DirectoryObject(key = Callback(ShowsMenu, category = category, show_title = show_title, show_id = show_id), title = show_title))

  return oc

####################################################################################################
@route(PREFIX + '/ShowsMenu', category=str, show_title=str, show_id=str)
def ShowsMenu(category, show_title, show_id):
  Log("Shows Menu ()")
  oc = ObjectContainer(title1 = category, title2 = show_title)
  
  episode_playlist_base = "http://www.skai.gr/Ajax.aspx?m=Nv.SqlModule&name=player_media_list_cat&pg=" 
  episode_playlist_start_url = episode_playlist_base + "1" + "&categoryid=" + show_id[0]  + "&mediatype=TV"
  Log("ShowsMenu -> episode_playlist_start_url: %s " % episode_playlist_start_url)
  
  ajax = HTML.ElementFromURL(episode_playlist_start_url)
  
  pages = ajax.xpath('//a[contains(@href, "javascript:loaditemscatlist")]/text()')
  if len(pages) > 1:
    pages = map(int, pages)
    num_pages = max(pages)
    if int(num_pages) > 2: num_pages = "2"
  else:
    num_pages = "1"
  Log("ShowsMenu -> num_pages: %s " % num_pages)
  for i in xrange(int(num_pages)):
    playlist_page_url = episode_playlist_base + str(i +1) + "&categoryid=" +show_id[0] + "&mediatype=TV"  
    playlist_page = HTML.ElementFromURL(playlist_page_url)
    episodes = playlist_page.xpath('//*[@class="playlist-item"]')
    Log("ShowsMenu -> episodes: %s " % episodes)
    for episode in episodes:
      episode_page_url = BASE_URL + episode.xpath('@href')[0]
      Log("ShowsMenu -> episode_page_url: %s" % episode_page_url)
      episode_thumb = episode.xpath('.//figure/img/@src')[0]
      Log("ShowsMenu -> episode_thumb: %s" % episode_thumb)
      episode_title = episode.xpath('.//figure/img/@alt')[0]
      Log("ShowsMenu -> episode_title: %s" % episode_title)
      episode_air_date = episode.xpath('.//div/p/time/text()')[0]
      Log("ShowsMenu -> episode_air_date: %s" % episode_air_date)
      episode_ID = RE_EPISODE_ID.search(episode_page_url).group(1)
      Log("ShowsMenu -> episode_ID: %s" % episode_ID)
      
      episode_summary,episode_video_url = GetVidInfo(episode_page_url)
      
      oc.add(CreateEpisodeObject(episode_title, episode_summary, episode_thumb, episode_video_url))   
 
  return oc

# check https://forums.plex.tv/discussion/114574/hppt-mp4-issue
# https://github.com/mikedm139/IMDb-Trailers.bundle/blob/master/Contents/Code/__init__.py#L58-L101

####################################################################################################
def GetVidInfo(url):
  clip_html = HTML.ElementFromURL(url)
  try:
    clip_summary = clip_html.xpath('//*[@class="stage-info"]/article/p/text()')[0]
  except:
    clip_summary = "No Summary"
  Log("GetVidInfo -> clip_summary: %s" % clip_summary)
  clip_url = clip_html.xpath('//*[@id="p-file"]/text()')[0]
  Log("GetVidInfo -> clip_url: %s" % clip_url)
  return clip_summary, clip_url

####################################################################################################
@route(PREFIX+'/episode')
def CreateEpisodeObject(title, summary, thumb, episode_video_url, include_container=False):  
  trailer = MovieObject(
    key = Callback(CreateEpisodeObject, title=title, summary=summary, thumb=thumb, episode_video_url=episode_video_url, include_container=True),
    rating_key = episode_video_url,
    title = title,
    summary = summary,
    thumb = thumb,
    items = [MediaObject(
      parts = [PartObject(
        key=Callback(
          PlayVideo, 
          episode_video_url=episode_video_url
          )
        )]
      )]
    )

  if include_container:
    return ObjectContainer(objects=[trailer])
  else:
    return trailer

####################################################################################################
def PlayVideo(episode_video_url):
  return Redirect(episode_video_url)

####################################################################################################
