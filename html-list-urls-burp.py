from burp import IBurpExtender, IContextMenuFactory
from javax.swing import JMenuItem
from java.awt.event import ActionListener
from java.io import PrintWriter
import os
import json

class BurpExtender(IBurpExtender, IContextMenuFactory, ActionListener):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        callbacks.setExtensionName("URL Organizer")
        self._stdout = PrintWriter(callbacks.getStdout(), True)
        callbacks.registerContextMenuFactory(self)

    def createMenuItems(self, invocation):
        menu_list = []
        menu_item = JMenuItem("Generate URL Organizer HTML", actionPerformed=self.generateHTML)
        menu_list.append(menu_item)
        return menu_list

    def generateHTML(self, event):
        sitemap = self._callbacks.getSiteMap(None)
        urls = [self._helpers.analyzeRequest(item.getHttpService(), item.getRequest()).getUrl().toString() for item in sitemap if self._callbacks.isInScope(self._helpers.analyzeRequest(item.getHttpService(), item.getRequest()).getUrl())]

        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'url_export.html')
        with open(desktop_path, 'w') as file:
            file.write('<html><head><title>URLs Observed</title></head><body>')
            file.write('<h1>URL Observed</h1>')
            file.write('<div id="urlContainer"></div>')
            file.write('<script>')
            file.write('var urls = ' + json.dumps(urls) + ';')  # Use json.dumps here
            file.write("""
            document.addEventListener('DOMContentLoaded', function() {
                var urlContainer = document.getElementById('urlContainer');
                var organizedUrls = urls.reduce(function(accumulator, url) {
                    var parser = document.createElement('a');
                    parser.href = url;
                    var parts = parser.pathname.split('/').filter(Boolean);
                    var current = accumulator;
                    parts.forEach(function(part, i) {
                        if (!current[part]) {
                            current[part] = i === parts.length - 1 ? [] : {};
                        }
                        current = current[part];
                    });
                    if (Array.isArray(current)) {
                        current.push(url);
                    }
                    return accumulator;
                }, {});
                function createList(obj) {
                    var ul = document.createElement('ul');
                    for (var key in obj) {
                        var li = document.createElement('li');
                        if (Array.isArray(obj[key])) {
                            li.appendChild(document.createTextNode(key + ' (' + obj[key].length + ' URLs)'));
                            var innerUl = document.createElement('ul');
                            obj[key].forEach(function(url) {
                                var innerLi = document.createElement('li');
                                var link = document.createElement('a');
                                link.href = url;
                                link.textContent = url;
                                innerLi.appendChild(link);
                                innerUl.appendChild(innerLi);
                            });
                            li.appendChild(innerUl);
                        } else {
                            li.appendChild(document.createTextNode(key));
                            li.appendChild(createList(obj[key]));
                        }
                        ul.appendChild(li);
                    }
                    return ul;
                }
                urlContainer.appendChild(createList(organizedUrls));
            });
            """)
            file.write('</script>')
            file.write('</body></html>')

        self._stdout.println("HTML file with URL organizer generated on Desktop.")
