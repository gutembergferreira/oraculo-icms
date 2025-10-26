from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.page import Page


class PageService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create(self, slug: str, *, default_title: str, default_content: str) -> Page:
        page = self.session.query(Page).filter(Page.slug == slug).one_or_none()
        if page:
            return page
        page = Page(slug=slug, title=default_title, content=default_content)
        self.session.add(page)
        self.session.flush()
        return page

    def update(self, page: Page, *, title: str, content: str, user_id: int | None) -> Page:
        page.title = title
        page.content = content
        page.updated_by_id = user_id
        self.session.add(page)
        self.session.flush()
        return page
