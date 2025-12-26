(define (problem w1) (:domain western-type)

(:objects
  ; ranch - place
  ; hank - rancher
  ; timmy - son
  ; carl - sheriff
  ; railwaydeveloper - character  
  ; antivenom - item
  ; snakebite - sickness
  ; generalstore - place
  ; theRanch - ranch
  ; theFarm - ranch
  ; theSaloon - saloon
  ; theCity - city
  ; town - place
  ; theFarmer - dairyfarmer
  ; theSon - son
  ; theRanger - texasranger
)

(:init
  (alive theFarmer)
  (at theFarmer theFarm)
  (owns theFarmer theFarm)
  (healthy theFarmer)
  (has-medicine theFarmer)

  (alive theSon)
  (at theSon ranch_place)
  (family theFarmer theSon)
  (healthy theSon)

  (theFarmChar hank)
  (theMover hank)
  (theCriminal railwaydeveloper)
  (theInvalid timmy)
  (theArrester Carl)
  (alive theRanger)
  (at theRanger town)
  (healthy theRanger)

  ; Hank lives on his ranch and loves his son.
  (alive hank)
  (at hank ranch_place)
  (owns hank ranch_place)
  (has hank antivenom)
  (has-medicine hank)
  (healthy hank)
  
  ; Timmy is Hank's son, and also lives at the ranch.
  (alive timmy)
  (at timmy ranch_place)
  (family hank timmy)
  (healthy timmy)

  ; Carl is the manager of the town general store.
  (alive carl)
  (at carl generalstore)
  (has-cash carl)
  (healthy carl)

  (has-cash railwaydeveloper)
  (healthy railwaydeveloper)
  (at railwaydeveloper theSaloon)

  (wants railwaydeveloper ranch_place)
  (autumn)
  (has-firewood hank)
)

(:goal  (and 
      (exists (?c - character) (not (alive ?c)))
      (exists (?c - character) (arrested ?c))
      (exists (?c - character ?l - place) (owns ?c ?l))
    )
)
)

