import { useEffect } from "react";
import { smokeTestGyms } from "./api/smoke";

export function App() {

  useEffect(() => {
    console.log("App mounted - running GymDB smoke test");

    smokeTestGyms().catch((err) => {
      console.error("Smoke test failed:", err);
    });
  }, []);

  return <div>GYMDB</div>
}
