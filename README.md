# GLClient

GLClient is the client part of a larger Whistleblowing project called [GlobaLeaks](https://github.com/globaleaks/GlobaLeaks/wiki/) and is mainly developed using [AngularJS](http://angularjs.org/).

More information can be found at:
- [GlobaLeaks documentation](https://github.com/globaleaks/GlobaLeaks/wiki)
- [GLBackend documentation](https://github.com/globaleaks/GLBackend/wiki)
- [GLClient documentation](https://github.com/globaleaks/GLClient/wiki)

## People who 'git clone GLClient'

- [Setting up development environment](https://github.com/globaleaks/GlobaLeaks/wiki/Setting-up-development-environment)

### Immediate command TODO

   npm install -d
   bower update -f

To build compressed and uglify GLClient:

   grunt build

### Developer remind

   $ grunt updateTranslations
   Running "updateTranslationsSource" task
   Warning: ENOENT, no such file or directory 'pot/en.po' Use --force to continue.
   Aborted due to warnings.

need to be fixed with: [mv globaleaks\_glclient-02-enpo.pot pot/en.po](https://www.transifex.com/projects/p/globaleaks/resource/glclient-02-enpo/download/pot/)

## License
Copyright (C) 2011-2014 Hermes No Profit Association - GlobaLeaks Project

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
