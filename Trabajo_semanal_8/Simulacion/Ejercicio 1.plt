[AC Analysis]
{
   Npanes: 3
   {
      traces: 1 {524290,0,"V(in)/(-I(V1))"}
      X: (' ',0,0.001,0,100)
      Y[0]: (' ',0,0.001,10,1)
      Y[1]: (' ',0,-90,30,90)
      Log: 1 2 0
      GridStyle: 1
      PltMag: 1
      PltPhi: 1 0
   },
   {
      traces: 2 {524291,0,"V(polo_real)"} {524292,0,"V(polos_complejos)"}
      X: (' ',0,0.001,0,100)
      Y[0]: (' ',0,0.00001,20,2)
      Y[1]: (' ',0,-180,45,0)
      Log: 1 2 0
      GridStyle: 1
      PltMag: 1
      PltPhi: 1 0
   },
   {
      traces: 1 {524293,0,"V(in)/V(base_ceros)"}
      X: (' ',0,0.001,0,100)
      Y[0]: (' ',0,0.1,20,1000000)
      Y[1]: (' ',0,0,45,180)
      Log: 1 2 0
      GridStyle: 1
      PltMag: 1
      PltPhi: 1 0
   }
}
