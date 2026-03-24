from fastapi import APIRouter, Depends
from admin.deps import get_current_admin

router = APIRouter(
    prefix='/admin',
    tags=['Admin'],
    dependencies=[Depends(get_current_admin)]
)

@router.post('/profile')
def admin():
    return {'admin are authenticated'}