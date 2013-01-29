# -*- coding: utf-8 -*-
"""Person.
"""

from five import grok
from plone.directives import dexterity

from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

from Products.CMFCore.utils import getToolByName

from plone.indexer import indexer
from plone.uuid.interfaces import IUUID

from plone.app.viewletmanager.manager import (
    OrderedViewletManager,
    ManageViewlets
)

from plone.app.content.interfaces import INameFromTitle

from collective.roster.interfaces import IPerson


class NameFromTitle(grok.Adapter):
    grok.provides(INameFromTitle)
    grok.context(IPerson)

    @property
    def title(self):
        return u"%s %s" % (self.context.last_name,
                           self.context.first_name)


@indexer(IPerson)
def title(context):

    title = INameFromTitle(context).title

    adapted = IPerson(context, None)

    if adapted:
        bound = IPerson["salutation"].bind(adapted)
        salutation = bound.get(adapted)
        if salutation:
            title = u"%s, %s" % (title, salutation)

    # XXX: We are mutating object during indexing... by purpose.
    context.title = title
    # Note: If binding and setting through the schema is so cool, why not here?
    # Because the field to be set is meant to be readonly on forms and setting
    # through the schema would explicitly prevent setting readonly fields.

    return title.encode("utf-8")  # XXX: unicode could crash the indexing

grok.global_adapter(title, name="Title")


@indexer(IPerson)
def subject(context):
    vocabulary_factory = getUtility(IVocabularyFactory,
                                    name="collective.roster.localgroups")
    vocabulary = vocabulary_factory(context)

    terms = filter(lambda term: term.value in context.groups, vocabulary)
    groups = map(lambda term: term.title.encode("utf-8"), terms)

    return context.subject + tuple(groups)
grok.global_adapter(subject, name="Subject")


class View(dexterity.DisplayForm):
    """ Person main view, which mainly renders the person viewlet manager """

    grok.context(IPerson)
    grok.require("zope2.View")
    grok.name("view")


class PersonViewlets(OrderedViewletManager, grok.ViewletManager):
    """ Person viewlet manager, which manages all person related viewlets """
    grok.context(IPerson)
    grok.name("collective.roster.personviewlets")


class ManagePersonViewlets(View, ManageViewlets):
    grok.context(IPerson)
    grok.name("manage-viewlets")

    def index(self):
        # ManageViewlets.__call__ may call this at its end, and then we'd like
        # to render by using our dexterity.DisplayForm based View-class.
        return View.__call__(self)

    def __call__(self):
        return ManageViewlets.__call__(self)


class GroupsViewlet(grok.Viewlet):
    """ Groups viewlet, which render list of groups the person belongs to """

    grok.viewletmanager(PersonViewlets)
    grok.context(IPerson)
    grok.name("collective.roster.personviewlets.localgroups")

    @property
    def groups(self):
        vocabulary_factory = getUtility(IVocabularyFactory,
                                        name="collective.roster.localgroups")
        vocabulary = vocabulary_factory(self.context)

        terms = filter(lambda term: term.value in self.context.groups,
                       vocabulary)
        titles = map(lambda term: term.title, terms)
        return titles


class PortraitViewlet(grok.Viewlet):
    """ Portrait viewlet, which renders the portrait image """

    grok.viewletmanager(PersonViewlets)
    grok.context(IPerson)
    grok.name("collective.roster.personviewlets.portrait")


class PublicationsViewlet(grok.Viewlet):
    """ Portrait viewlet, which renders the portrait the
        publications (tutkapages) """

    grok.viewletmanager(PersonViewlets)
    grok.context(IPerson)
    grok.name("collective.roster.personviewlets.publications")


class PersonViewlet(grok.Viewlet):
    """ Person viewlet, which renders the person image """

    grok.viewletmanager(PersonViewlets)
    grok.context(IPerson)
    grok.name("collective.roster.personviewlets.person")


class RelatedContentViewlet(grok.Viewlet):
    """ Related content viewlet, which renders list of content linked to the
    person """

    grok.viewletmanager(PersonViewlets)
    grok.context(IPerson)
    grok.name("collective.roster.personviewlets.relatedcontent")

    @property
    def related_items(self):
        pc = getToolByName(self.context, "portal_catalog")
        results = pc(related_persons=[IUUID(self.context)])
        return results
