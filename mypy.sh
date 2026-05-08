#!/bin/bash

CURRENT_DIR="$(pwd)"
# get the full path of the directory where the current script is:
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

RETVAL=0

echo "running $SCRIPT_DIR/mypy.sh"

export MYPYPATH="${SCRIPT_DIR}/stubs"
MYPY=(mypy --strict --no-incremental --show-error-codes --pretty)

echo cd "$SCRIPT_DIR/engine"
cd "$SCRIPT_DIR/engine" || exit 1
echo "${MYPY[@]}" ./*.py
"${MYPY[@]}" ./*.py
ENGINE_RETVAL=$?
if [ ${ENGINE_RETVAL} != 0 ] ; then
    RETVAL=$((${RETVAL} + ${ENGINE_RETVAL}))
fi

echo cd "$SCRIPT_DIR/setup"
cd "$SCRIPT_DIR/setup" || exit 1
echo "${MYPY[@]}" ../engine/{tabsqlitedb,it_util}.py ./*.py
"${MYPY[@]}" ../engine/{tabsqlitedb,it_util}.py ./*.py
SETUP_RETVAL=$?
if [ ${SETUP_RETVAL} != 0 ] ; then
    RETVAL=$((${RETVAL} + ${SETUP_RETVAL}))
fi

echo cd "$SCRIPT_DIR/tests"
cd "$SCRIPT_DIR/tests" || exit 1
echo "${MYPY[@]}" ../engine/{tabsqlitedb,it_util}.py ./test_*.py
"${MYPY[@]}" ../engine/{tabsqlitedb,it_util}.py ./test_*.py
SETUP_RETVAL=$?
if [ ${SETUP_RETVAL} != 0 ] ; then
    RETVAL=$((${RETVAL} + ${SETUP_RETVAL}))
fi

cd "$CURRENT_DIR" || exit 1
exit $RETVAL
