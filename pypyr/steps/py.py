"""pypyr step that executes a string as python.

Uses python's exec() to evaluate and execute arbitrary python code.
"""
import builtins
import logging

from pypyr.moduleloader import _ChainMapPretendDict

# logger means the log level will be set correctly
logger = logging.getLogger(__name__)


def run_step(context):
    """Execute dynamic python code.

    Takes two forms of input:
        py: exec contents as dynamically interpreted python statements, with
            contents of context available as vars.
        pycode: exec contents as dynamically interpreted python statements,
            with the context object itself available as a var.

    Args:
        context (pypyr.context.Context): Mandatory.
            Context is a dictionary or dictionary-like.
            Context must contain key 'py' or 'pycode'
    """
    logger.debug("started")

    if 'pycode' in context:
        exec_pycode(context)
    else:
        context.assert_key_has_value(key='py', caller=__name__)
        # ChainMap necessary evil. If you separate global + local scope here,
        # nested scopes & free variables stop working (e.g nested list
        # comprehensions). Don't want to put context itself as globals -
        # because any imports or new vars in exec source will end up in globals
        # and thus pollute context with unwanted keys.
        # e.g 'import math; x=math.sqrt(4)'
        # will result in 'math' and 'x' in context.
        # want to avoid having to deepcopy context here too
        first_dict = {}
        # first_dict gets any adds/imports, not the 2nd dict which is context.
        # other than this, first_dict behaves like locals, basically.
        globals = _ChainMapPretendDict(first_dict,
                                       context)
        # the save function ref allows pipeline to use save to persist vars
        # back to context,
        first_dict['save'] = get_save(context, globals)

        exec(context['py'], globals)

    # logger.debug("exec output context merged with pipeline context")

    logger.debug("done")


def exec_pycode(context):
    """Exec contents of pycode.

    This form of execute means pycode does not have the contents of context in
    the exec namespace, so referencing context needs to do:
        a = context['myvar']

    Rather than just
        a = myvar

    Args:
        context (pypyr.context.Content): context containing `pycode` key.

    Returns:
        None. Any mutations to content is on the input arg instance itself.
    """
    context.assert_key_has_value(key='pycode', caller=__name__)

    logger.debug("Executing python string: %s", context['pycode'])
    exec(context['pycode'], {'__builtins__': builtins.__dict__,
                             'context': context})


def get_save(context, namespace):
    """Return save function reference."""
    def save(*args, **kwargs):
        """Save variables in exec namespace back to context.

        Args:
            context: instance of context to which to save vars from namespace.
            namespace: set var values from this namespace.

        Returns:
            None. Mutates context.
        """
        d = {}
        for arg in args:
            try:
                d[arg] = namespace[arg]
            except KeyError as err:
                raise KeyError(f"Trying to save '{arg}', but can't find it "
                               "in the py step scope. Remember it should be "
                               "save('key'), not save(key) - mind the "
                               "quotes.") from err

        # kwargs is {} if not set, no None worries.
        d.update(**kwargs)
        context.update(d)

    return save
