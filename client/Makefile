MOCHA_OPTS=
REPORTER = list

check: test

test: test-unit

test-unit:
	@NODE_ENV=test ./node_modules/.bin/mocha \
	--reporter $(REPORTER) api/specification.js

