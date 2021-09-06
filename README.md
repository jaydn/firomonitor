# firomonitor

## Installation
- `git clone https://github.com/jaydn/firomonitor.git`
- Create your versions of all the config files with your desired options
  - cfg/firomonitor/config.json
  - cfg/firod/firo.conf
- Create your version of docker-compose.yml with secrets replaced with your own
- `docker-compose up -d`
- Your Firomonitor web UI is now exposed on port 80

## Admin
### Taking it down
`docker-compose down`

### Mailing
There is new parameter `should_send_mail` in cfg/firomonitor/config.json

To load up a new config you need to rebuild the scraper like this
1. `docker-compose stop firomon-scraper`
2. `docker-compose up -d --build firomon-scraper`

If `should_send_mail` is true it will just tell you when it would mail instead of doing it

### Logs
Use `docker-compose logs`

Example: to follow latest status of all containers `docker-compose logs --tail=1 -f`
