import { GymsService } from "./index";

export async function smokeTestGyms() {
    const response = await GymsService.listGymsV2V2GymsGet(
        undefined,  // region
        undefined,  // minConf
        1,          // limit
        0           // offset
    );
    console.log("GymDB /v2/gyms response:", response);
}