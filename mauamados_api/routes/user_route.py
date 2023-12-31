from typing import List
from fastapi import HTTPException, APIRouter, Response, Query, Path, FastAPI
import json
from config.database import collection_name_user
from models.user_model import User, UpdateUser
from schemas.user_schema import user_serializer, users_serializer
from bson import ObjectId
from passlib.context import CryptContext
from services.services import is_user_over_eighteen, validar_login, validate_password, email_exists
from fastapi import Body



user_api_router = APIRouter()


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@user_api_router.get("/user")
async def get_users():
    users = users_serializer(collection_name_user.find())
    return users

@user_api_router.get("/user/{ma_id}")
async def get_user(ma_id: int):
    return users_serializer(collection_name_user.find({"ma_id":ma_id}))


@user_api_router.post("/users")
async def create_users(users: list[User]):
    created_users = []
    for user in users:
        if not is_user_over_eighteen(user.age):
            raise HTTPException(status_code=400, detail="Apenas usuários maiores de 18 podem criar a conta")

        if not validate_password(user.senha):
            raise HTTPException(status_code=400, detail="Senha deve ter ao menos 8 caracteres")
        
        if not validar_login(user.login):
            raise HTTPException(status_code=400, detail="login deve ter @maua.br")
        

        # Hash da senha usando bcrypt
        hashed_password = password_context.hash(user.senha)
        
        # Substituir a senha do usuário pelo hash gerado
        user.senha = hashed_password

        _id = collection_name_user.insert_one(dict(user))
        created_users.append(collection_name_user.find_one({"_id": _id.inserted_id}))

        def send_mail():
            print("Um email de segurança foi enviado para o @maua.br do usuário")

    return users_serializer(created_users)

@user_api_router.post("/user")
async def create_user(user: User):
    if not is_user_over_eighteen(user.age):
        raise HTTPException(status_code=400, detail="Apenas usuários maiores de 18 podem criar a conta")

    if not validate_password(user.senha):
        raise HTTPException(status_code=400, detail="Senha deve ter ao menos 8 caracteres")
    
    if not validar_login(user.login):
        raise HTTPException(status_code=400, detail="login deve ter @maua.br")

    # Hash da senha usando bcrypt
    hashed_password = password_context.hash(user.senha)
    
    # Substituir a senha do usuário pelo hash gerado
    user.senha = hashed_password

    _id = collection_name_user.insert_one(dict(user))
    created_user = collection_name_user.find_one({"_id": _id.inserted_id})

    def send_mail():
        print("Um email de segurança foi enviado para o @maua.br do usuário")

    return user_serializer(created_user) 

@user_api_router.delete("/delete_all_users")
async def delete_all_users():
    collection_name_user.delete_many({})
    return {"Daniel, fique tranquilo": "Todos os usuários foram deletados com sucesso!!!"}


@user_api_router.delete("/user/delete_user/{ma_id}")
async def delete_user(ma_id: int):
    collection_name_user.delete_one({"ma_id": ma_id})
    return {"Daniel, fique tranquilo": "O usuário foi deletado com sucesso!!!"}


@user_api_router.put("/user/{ma_id}")
async def update_user(ma_id: int, user: UpdateUser):
    if user.ma_id is not None:
        return{"POXA DANIEL!!!": "Por favor não altere o ma_id, vai destruir a database"}
    if user.name is not None:
        collection_name_user.find_one_and_update({"ma_id": ma_id}, {"$set": {'name': user.name}})
    if user.profile_picture is not None:
        collection_name_user.find_one_and_update({"ma_id": ma_id}, {"$push": {'profile_picture': user.profile_picture}})
    if user.age is not None:
        collection_name_user.find_one_and_update({"ma_id": ma_id}, {"$set": {'age': user.age}})
    if user.course is not None:
        collection_name_user.find_one_and_update({"ma_id": ma_id}, {"$set": {'course': user.course}})
    if user.bio is not None:
        collection_name_user.find_one_and_update({"ma_id": ma_id}, {"$set": {'bio': user.bio}})
    if user.genero is not None:
        collection_name_user.find_one_and_update({"ma_id": ma_id}, {"$set": {'genero': user.genero}})
    if user.sexual_orientation is not None:
        collection_name_user.find_one_and_update({"ma_id": ma_id}, {"$set": {'sexual_orientation': user.sexual_orientation}})
    if user.tags_preferences is not None:
        collection_name_user.find_one_and_update({"ma_id": ma_id}, {"$push": {'tags_preferences': {"$each": user.tags_preferences}}})
    if user.match is not None:
        collection_name_user.find_one_and_update({"ma_id": ma_id}, {"$push": {'match': {"$each": user.match}}})
    if user.likes is not None:
        collection_name_user.find_one_and_update({"ma_id": ma_id}, {"$push": {'likes': {"$each": user.likes}}})
    if user.login is not None:
        collection_name_user.find_one_and_update({"ma_id": ma_id}, {"$set": {'login': user.login}})
    if user.senha is not None:
        collection_name_user.find_one_and_update({"ma_id": ma_id}, {"$set": {'senha': user.senha}})
    return  users_serializer(collection_name_user.find({"ma_id": ma_id}))

@user_api_router.delete("/user/{ma_id}")
async def delete_user(ma_id:int):
    collection_name_user.find_one_and_delete({"ma_id": ma_id})
    return {"status": "ok"}

@user_api_router.get("/user/matches/{ma_id}")
async def get_matches(ma_id: int):
    query = collection_name_user.find_one({"ma_id": ma_id}, {"match": 1, "_id": 0})
    matches = query.get('match', [])
    return Response(content=json.dumps(matches), media_type="application/json")


@user_api_router.get("/user/likes/{ma_id}")
async def get_likes(ma_id:int):
    query = collection_name_user.find_one({"ma_id": ma_id},{"likes":1,"_id":0})
    likes = query.get('likes',[])
    return Response(content=json.dumps(likes),media_type="application/json")


#var url = Uri.parse('http://127.0.0.1:8000/login/?username=$username&password=$password');
@user_api_router.get("/login/")
async def login(username: str, password: str):
    # Encontrar o usuário no banco de dados pelo nome de usuário
    user_data = collection_name_user.find_one({"login": username}, {"ma_id": 1, "senha": 1})

    if user_data:
        # Verificar a senha usando a função verify do CryptContext
        if password_context.verify(password, user_data["senha"]):
            return {"ID": str(user_data["ma_id"])}
        else:
            raise HTTPException(status_code=401, detail="Senha incorreta")
    else:
        raise HTTPException(status_code=404, detail="Username not found")
    

@user_api_router.get("/user/senha/{ma_id}")
async def get_senha(ma_id:int):
    query = collection_name_user.find_one({"ma_id":ma_id},{"senha":1,"_id":0})
    senha = query.get('senha',[])
    return Response(content=json.dumps(senha),media_type="application/json")


@user_api_router.post("/user/post_like/{ma_id}/{like_id}")
async def post_like(ma_id: int, like_id: str):
    # Assuming you have imported and initialized collection_name_user properly
    collection_name_user.update_many(
        {"ma_id": ma_id},
        {"$push": {"likes": {"$each": [like_id]}}}
    )
    return {"Daniel, fique tranquilo": "O Like foi adicionado com sucesso!!!"}

@user_api_router.get("/user/get_possible_matches/{ma_id}")
async def get_info(ma_id: int):
    # Get genero, match list, like list, sexual orientation
    query = collection_name_user.find_one(
        {"ma_id": ma_id},
        {"genero": 1, "match": 1, "likes": 1, "sexual_orientation": 1, "_id": 0},
    )

    if query:
        sexual_orientation = query.get("sexual_orientation")
        genero = query.get("genero")

        

        if sexual_orientation == "Heterossexual" and genero=="Masculino":
            
            matches_query = {"genero": "Feminino", "sexual_orientation":["Heterossexual", "Bissexual"]} 

        elif sexual_orientation == "Heterossexual" and genero=="Feminino":
            
            matches_query = {"genero": "Masculino", "sexual_orientation":["Heterossexual", "Bissexual"]} 

        elif sexual_orientation == "Homossexual":
            
            matches_query = {"genero": query.get(genero), "ma_id": {"$ne": ma_id}}
        #caso n ache nada
        elif sexual_orientation == "Bissexual":
           
            matches_query = {"genero": {"$in": ["Masculino", "Feminino"]}, "ma_id": {"$ne": ma_id}}

        else:
           
            matches_query = {}

       
        match_list = list(query.get("match", []))
        like_list = list(query.get("likes", []))

        
        potential_matches = list(
    collection_name_user.find(
        {
            "ma_id": {"$ne": ma_id},  # Exclude the current user
            "genero": matches_query.get("genero"),
            # Remove "ma_id": {"$ne": ma_id} from here
            "ma_id": {"$nin": match_list + like_list},
        },
        {"_id": 0, "ma_id": 1, "name": 1, "profile_picture": 1, "age": 1, "course": 1, "bio": 1,
         "genero": 1, "sexual_orientation": 1, "tags_preferences": 1, "match": 1, "likes": 1,
         "login": 1, "senha": 1}
    )
)

        return Response(content=json.dumps(potential_matches), media_type="application/json")

    else:
        return Response(
            content=json.dumps({"error": "User not found"}),
            media_type="application/json",
            status_code=404,
        )

@user_api_router.put("/user/change_name/{ma_id}/{new_name}")
async def change_name(ma_id: int, new_name: str):
    collection_name_user.update_many(
        {"ma_id": ma_id},
        {"$set": {"name": new_name}}
    )
    return {"Daniel, fique tranquilo": "O nome foi alterado com sucesso!!!"}

@user_api_router.put("/user/change_age/{ma_id}/{new_age}")
async def change_age(ma_id: int, new_age: int):
    collection_name_user.update_many(
        {"ma_id": ma_id},
        {"$set": {"age": new_age}}
    )
    return {"Daniel, fique tranquilo": "A idade foi alterada com sucesso!!!"}


@user_api_router.post("/user/add_tag_preferences/{ma_id}/{new_tag}")
async def add_tags_preferences(ma_id: int, new_tag: str):
    collection_name_user.update_many(
        {"ma_id": ma_id},
        {"$push": {"tags_preferences": {"$each": [new_tag]}}}
    )
    return {"Daniel, fique tranquilo": "A tag foi adicionada com sucesso!!!"}

@user_api_router.delete("/user/remove_tag_preference/{ma_id}/{tag_to_delete}")
async def remove_tags_preference(ma_id:int, tag_to_delete:str):
    collection_name_user.update_many(
        {"ma_id": ma_id},
        {"$pull": {"tags_preferences": tag_to_delete}}
    )
    return {"Daniel, fique tranquilo": "A tag foi removida com sucesso!!!"}


@user_api_router.post("/user/add_photo/{ma_id}")
async def add_photo(ma_id: int, new_photo: str = Query(...)):
    collection_name_user.update_many(
        {"ma_id": ma_id},
        {"$push": {"profile_picture": {"$each": [new_photo]}}}
    )
    return {"Daniel, fique tranquilo": "A foto foi adicionada com sucesso!!!"}


@user_api_router.put("/user/photo_new_index/{ma_id}/{new_index}")
async def photo_new_index(ma_id: int, new_index: int, photo_to_change: str = Body(...)):
    collection_name_user.update_many(
        {"ma_id": ma_id},
        {"$pull": {"profile_picture": photo_to_change}}
    )
    collection_name_user.update_many(
        {"ma_id": ma_id},
        {"$push": {"profile_picture": {"$each": [photo_to_change], "$position": new_index}}}
    )
    return {"Daniel, fique tranquilo": "A foto foi alterada de posição com sucesso!!!"}


@user_api_router.delete("/user/delete_photo/{ma_id}")
async def delete_photo(ma_id: int, photo_to_delete: str = Body(...)):
    collection_name_user.update_many(
        {"ma_id": ma_id},
        {"$pull": {"profile_picture": photo_to_delete}}
    )
    return {"Daniel, fique tranquilo": "A foto foi deletada com sucesso!!!"}

@user_api_router.put("/user/change_course/{ma_id}/{new_course}")
async def change_course(ma_id: int, new_course: str):
    collection_name_user.update_many(
        {"ma_id": ma_id},
        {"$set": {"course": new_course}}
    )
    return {"Daniel, fique tranquilo": "O curso foi alterado com sucesso!!!"}

@user_api_router.put("/user/change_bio/{ma_id}/{new_bio}")
async def change_bio(ma_id: int, new_bio: str):
    collection_name_user.update_many(
        {"ma_id": ma_id},
        {"$set": {"bio": new_bio}}
    )
    return {"Daniel, fique tranquilo": "A bio foi alterada com sucesso!!!"}

@user_api_router.put("/user/change_genero/{ma_id}/{new_genero}")
async def change_genero(ma_id: int, new_genero: str):
    collection_name_user.update_many(
        {"ma_id": ma_id},
        {"$set": {"genero": new_genero}}
    )
    return {"Daniel, fique tranquilo": "O genero foi alterado com sucesso!!!"}

@user_api_router.put("/user/change_sexual_orientation/{ma_id}/{new_sexual_orientation}")
async def change_sexual_orientation(ma_id: int, new_sexual_orientation: str):
    collection_name_user.update_many(
        {"ma_id": ma_id},
        {"$set": {"sexual_orientation": new_sexual_orientation}}
    )
    return {"Daniel, fique tranquilo": "A orientação sexual foi alterada com sucesso!!!"}


@user_api_router.delete("/user/remove_like/{ma_id}/{like_id}")
async def remove_like(ma_id: int, like_id: str):
    user = collection_name_user.find_one({"ma_id": ma_id})
    likes = user.get("likes",[])
    if like_id in likes:
        likes.remove(like_id)

        collection_name_user.update_one(
            {"ma_id": ma_id},
            {"$set": {"likes": likes}}
        )

        return {"FOI DANEIL!!!": f"Removemos o like {like_id} com sucesso, a feinha perdeu sua chance"}

    else:
        return HTTPException(status_code=404,detail=f"Poxa Daniel!!!! Num deu pra remover o like {like_id}")
    
@user_api_router.put("/user/add_match/{ma_id}/{match_id}")
async def add_match(ma_id:int, match_id:str):
    user = collection_name_user.find_one({"ma_id": ma_id})
    likes = user.get("likes",[])
    if match_id in likes:
        matches = user.get("match",[])
        matches.append(match_id)
        collection_name_user.update_one(
            {"ma_id": ma_id},
            {"$set": {"match": matches}}
        )

        return{"FOI DANEIL!!!!" : f"Match com a gatinha {match_id} com sucesso, VAI DAR NAMORO!!!! =)"}
    else:
        return HTTPException(status_code=404,detail=f"Poxa Daniel!!!! Num deu pra adcionar o match {match_id}")

@user_api_router.delete("/user/remove_match/{ma_id}/{match_id}")
async def remove_match(ma_id:int, match_id:str):
    user = collection_name_user.find_one({"ma_id": ma_id})
    likes = user.get("likes",[])
    matches = user.get("match",[])
    if match_id in matches:
        matches.remove(match_id)
        likes.remove(match_id)
        collection_name_user.update_one(
            {"ma_id": ma_id},
            {"$set": {"match": matches}}
        )
        collection_name_user.update_one(
            {"ma_id": ma_id},
            {"$set": {"likes": likes}}
        )

        return{"FOI DANIEL!!!!": f"Uma pena, não vai dar namoro =(, a {match_id} era um piteuzinho"}
    else:
        return HTTPException(status_code=404,detail=f"Poxa Daniel!!!! Num deu pra remover o match {match_id}")